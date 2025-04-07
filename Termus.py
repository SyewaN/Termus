#!/usr/bin/env python3

import os
import sys
import subprocess
import glob
import random
import threading
import time
try:
    from colorama import init, Fore, Back, Style
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    
try:
    from mutagen import File
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

__version__ = "1.0.0"

class SimpleMusicPlayer:
    def __init__(self):
        # Colorama desteği varsa etkinleştir
        if COLORAMA_AVAILABLE:
            init(autoreset=True)
            
        # Banner göster
        self.show_banner()
        
        # Önce mpv'nin yüklü olup olmadığını kontrol et
        try:
            subprocess.run(['which', 'mpv'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            self.print_error("mpv yüklü değil. Lütfen 'sudo xbps-install -S mpv' komutu ile yükleyin.")
            sys.exit(1)
            
        # Playerctl kontrolü
        try:
            subprocess.run(['which', 'playerctl'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.playerctl_available = True
        except subprocess.CalledProcessError:
            self.playerctl_available = False
            self.print_warning("playerctl yüklü değil. İlerleme çubuğu özelliği devre dışı.")

        # Müzik klasörü
        self.music_dir = os.path.expanduser("~/Müzik")
        if not os.path.exists(self.music_dir):
            self.print_warning(f"{self.music_dir} klasörü bulunamadı. Lütfen müzik klasörünü 'dir' komutu ile ayarlayın.")
            
        # Desteklenen formatlar
        self.supported_formats = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        # Tüm şarkıları bul
        self.playlist = []
        self.refresh_playlist()
        # Durum değişkenleri
        self.current_song_index = 0
        self.playing = False
        self.player_process = None
        self.volume = 50  # Yüzde olarak
        self.repeat_mode = 0  # 0: Kapalı, 1: Tümünü Tekrarla, 2: Birini Tekrarla
        
        # Otomatik olarak şarkı değiştirmeyi kontrol etmek için
        self.player_checker = None
        self.should_stop = False
        self.progress_thread = None
        self.should_stop_progress = False

    def show_banner(self):
        """Program başlığını gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}======================================")
            print(f"{Fore.YELLOW}   Termus {__version__}")
            print(f"{Fore.GREEN}   Basit Konsol Müzik Oynatıcısı")
            print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
        else:
            print("====================================")
            print("   Termus " + __version__)
            print("   Basit Konsol Müzik Oynatıcısı")
            print("====================================")

    def print_info(self, message):
        """Bilgi mesajı gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.BLUE}[INFO] {message}{Style.RESET_ALL}")
        else:
            print(f"[INFO] {message}")
    
    def print_success(self, message):
        """Başarı mesajı gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")
        else:
            print(f"[OK] {message}")
            
    def print_warning(self, message):
        """Uyarı mesajı gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.YELLOW}[UYARI] {message}{Style.RESET_ALL}")
        else:
            print(f"[UYARI] {message}")
            
    def print_error(self, message):
        """Hata mesajı gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"{Fore.RED}[HATA] {message}{Style.RESET_ALL}")
        else:
            print(f"[HATA] {message}")

    def refresh_playlist(self):
        """Müzik dizininden tüm desteklenen müzik dosyalarını tarar"""
        self.playlist = []
        
        # Klasör mevcut değilse boş liste döndür
        if not os.path.exists(self.music_dir):
            return
            
        self.print_info(f"Müzik klasörü taranıyor: {self.music_dir}")
        for ext in self.supported_formats:
            pattern = os.path.join(self.music_dir, f"*{ext}")
            files = glob.glob(pattern)
            self.print_info(f"{ext} uzantılı {len(files)} dosya bulundu.")
            self.playlist.extend(files)
            
        # Alt klasörleri de tara
        for root, dirs, files in os.walk(self.music_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_formats):
                    full_path = os.path.join(root, file)
                    if full_path not in self.playlist:
                        self.playlist.append(full_path)
        
        self.playlist.sort()
        self.print_success(f"Toplam {len(self.playlist)} müzik dosyası bulundu.")

    def play(self):
        """Mevcut şarkıyı çalar"""
        if not self.playlist:
            self.print_warning("Çalma listesi boş.")
            return
            
        # Eğer zaten bir oynatıcı çalışıyorsa durdur
        self.stop()
        
        song_path = self.playlist[self.current_song_index]
        if COLORAMA_AVAILABLE:
            print(f"{Fore.GREEN}Çalınıyor: {Fore.WHITE}{os.path.basename(song_path)}")
        else:
            print(f"Çalınıyor: {os.path.basename(song_path)}")
        
        # mpv ile çal
        try:
            self.player_process = subprocess.Popen(
                ['mpv', '--no-video', f'--volume={self.volume}', song_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.playing = True
            
            # Oynatıcı durumunu kontrol eden thread'i başlat
            self.start_player_checker()
            
            # İlerleme çubuğunu başlat
            if self.playerctl_available:
                self.start_progress_display()
            
        except Exception as e:
            self.print_error(f"Oynatma hatası: {e}")
            self.playing = False

    def start_player_checker(self):
        """Oynatıcının durumunu kontrol eden thread'i başlatır"""
        if self.player_checker is not None:
            return
            
        self.should_stop = False
        self.player_checker = threading.Thread(target=self.check_player_loop)
        self.player_checker.daemon = True
        self.player_checker.start()
        
    def check_player_loop(self):
        """Sürekli olarak oynatıcı durumunu kontrol eder"""
        while not self.should_stop:
            if self.playing and self.player_process:
                # Oynatıcı hala çalışıyor mu kontrol et
                if self.player_process.poll() is not None:
                    # Süreç tamamlandı
                    self.playing = False
                    
                    # Şarkı modu kontrolü
                    if self.repeat_mode == 2:  # Bir şarkıyı tekrarla
                        self.play()
                    elif self.repeat_mode == 1 or self.repeat_mode == 0:  # Tümünü tekrarla veya tekrarlama kapalı
                        self.next_song()
                        if self.repeat_mode == 1 or self.current_song_index > 0:  # Tümünü tekrarla veya son şarkı değilse çal
                            self.play()
            time.sleep(1)  # Her saniye kontrol et
    
    def start_progress_display(self):
        """İlerleme çubuğunu gösteren thread'i başlatır"""
        if self.progress_thread is not None:
            return
            
        self.should_stop_progress = False
        self.progress_thread = threading.Thread(target=self.progress_display_loop)
        self.progress_thread.daemon = True
        self.progress_thread.start()
    
    def progress_display_loop(self):
        """Şarkı ilerlemesini gösteren döngü"""
        # mpv'nin başlaması için biraz bekle
        time.sleep(2)
        
        while not self.should_stop_progress and self.playing:
            try:
                # Şarkı süresi ve pozisyonu al
                # Not: Bazı şarkılar için bu bilgi alınamayabilir
                duration_cmd = ['playerctl', 'metadata', '--player=mpv', 'mpris:length']
                duration_output = subprocess.check_output(duration_cmd, stderr=subprocess.DEVNULL).decode().strip()
                duration = int(duration_output) / 1000000  # mikrosaniye -> saniye
                
                position_cmd = ['playerctl', 'position', '--player=mpv']
                position_output = subprocess.check_output(position_cmd, stderr=subprocess.DEVNULL).decode().strip()
                position = float(position_output)
                
                # İlerleme çubuğu oluştur
                width = 40
                progress = int(width * position / duration) if duration > 0 else 0
                
                # İlerleme çubuğunu ve zamanı yazdır
                if COLORAMA_AVAILABLE:
                    bar = f"{Fore.GREEN}{'█' * progress}{Fore.WHITE}{'░' * (width - progress)}"
                else:
                    bar = f"{'█' * progress}{'░' * (width - progress)}"
                
                time_info = f"{int(position // 60):02d}:{int(position % 60):02d}/{int(duration // 60):02d}:{int(duration % 60):02d}"
                
                # Oynatma modunu göster
                modes = ["Normal", "Tümünü Tekrarla", "Birini Tekrarla"]
                mode_text = modes[self.repeat_mode]
                
                # Durum satırını yazdır
                status_line = f"\r{bar} {time_info} | Ses: %{self.volume} | Mod: {mode_text}"
                print(status_line, end="")
                
            except Exception:
                # Playerctl hatası veya mpv henüz hazır değil
                pass
                
            time.sleep(1)
        
        # İlerleme çubuğu durdurulduğunda satırı temizle
        print("\r" + " " * 80 + "\r", end="")
    
    def stop_progress_display(self):
        """İlerleme çubuğunu durduran fonksiyon"""
        self.should_stop_progress = True
        if self.progress_thread:
            time.sleep(1)  # Thread'in temiz bir şekilde sonlanmasını bekle
            self.progress_thread = None

    def stop_player_checker(self):
        """Oynatıcı durumunu kontrol eden thread'i durdurur"""
        self.should_stop = True
        if self.player_checker:
            self.player_checker = None

    def stop(self):
        """Müziği durdurur"""
        if self.player_process and self.playing:
            self.stop_progress_display()
            self.player_process.terminate()
            self.player_process.wait()
            self.player_process = None
            self.playing = False
            self.print_info("Durduruldu.")

    def next_song(self):
        """Sonraki şarkıya geçer"""
        if self.playlist:
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist)
            if self.playing:
                self.play()
            else:
                self.print_info(f"Sonraki şarkı: {os.path.basename(self.playlist[self.current_song_index])}")

    def prev_song(self):
        """Önceki şarkıya geçer"""
        if self.playlist:
            self.current_song_index = (self.current_song_index - 1) % len(self.playlist)
            if self.playing:
                self.play()
            else:
                self.print_info(f"Önceki şarkı: {os.path.basename(self.playlist[self.current_song_index])}")

    def set_volume(self, volume):
        """Ses seviyesini ayarlar (0-100 arası)"""
        self.volume = max(0, min(100, volume))
        if COLORAMA_AVAILABLE:
            print(f"{Fore.BLUE}Ses seviyesi: {Fore.WHITE}%{self.volume}")
        else:
            print(f"Ses seviyesi: %{self.volume}")
        
        # Eğer müzik çalıyorsa ses seviyesini güncelle (mpv yeniden başlatılarak)
        if self.playing:
            current_song = self.playlist[self.current_song_index]
            self.stop()
            self.play()

    def volume_up(self):
        """Ses seviyesini artırır"""
        self.set_volume(self.volume + 10)

    def volume_down(self):
        """Ses seviyesini azaltır"""
        self.set_volume(self.volume - 10)

    def shuffle(self):
        """Çalma listesini karıştırır"""
        if self.playlist:
            current_song = self.playlist[self.current_song_index]
            random.shuffle(self.playlist)
            # Mevcut şarkıyı bul
            try:
                self.current_song_index = self.playlist.index(current_song)
            except ValueError:
                self.current_song_index = 0
            self.print_success("Çalma listesi karıştırıldı.")

    def toggle_repeat_mode(self):
        """Tekrar modunu değiştirir: Kapalı -> Tümünü Tekrarla -> Birini Tekrarla -> Kapalı"""
        self.repeat_mode = (self.repeat_mode + 1) % 3
        modes = ["Kapalı", "Tümünü Tekrarla", "Birini Tekrarla"]
        if COLORAMA_AVAILABLE:
            print(f"{Fore.MAGENTA}Tekrar modu: {Fore.WHITE}{modes[self.repeat_mode]}")
        else:
            print(f"Tekrar modu: {modes[self.repeat_mode]}")

    def get_current_song_name(self):
        """Mevcut şarkının adını döndürür"""
        if self.playlist:
            return os.path.basename(self.playlist[self.current_song_index])
        return "Şarkı yok"

    def search_song(self, query):
        """Şarkı listesinde arama yapar"""
        query = query.lower()
        results = []
        
        for i, song in enumerate(self.playlist):
            song_name = os.path.basename(song).lower()
            if query in song_name:
                results.append((i, song))
        
        if not results:
            self.print_warning("Sonuç bulunamadı.")
            return
        
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.YELLOW}==== Arama Sonuçları ===={Style.RESET_ALL}")
        else:
            print("\n==== Arama Sonuçları ====")
            
        for i, (index, song) in enumerate(results):
            if COLORAMA_AVAILABLE:
                print(f"{i+1}. {Fore.GREEN}{os.path.basename(song)}")
            else:
                print(f"{i+1}. {os.path.basename(song)}")
        
        print("\nÇalmak için numara girin (veya iptal için boş bırakın):")
        selection = input("> ").strip()
        
        if selection and selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(results):
                self.current_song_index = results[idx][0]
                self.play()
                
    def show_song_info(self):
        """Çalan şarkının metadata bilgilerini gösterir"""
        if not self.playlist:
            self.print_warning("Çalma listesi boş.")
            return
        
        if not MUTAGEN_AVAILABLE:
            self.print_warning("Mutagen kütüphanesi yüklü değil. Şarkı bilgileri gösterilemiyor.")
            self.print_info("Mutagen'i yüklemek için: pip install mutagen")
            return
            
        song_path = self.playlist[self.current_song_index]
        try:
            audio = File(song_path)
            if COLORAMA_AVAILABLE:
                print(f"\n{Fore.YELLOW}========== Şarkı Bilgileri =========={Style.RESET_ALL}")
            else:
                print("\n========== Şarkı Bilgileri ==========")
            
            print(f"Dosya: {os.path.basename(song_path)}")
            
            if hasattr(audio, 'tags') and audio.tags:
                # ID3 etiketleri (MP3)
                tags = audio.tags
                if 'TPE1' in tags:  # Sanatçı
                    if COLORAMA_AVAILABLE:
                        print(f"{Fore.CYAN}Sanatçı: {Fore.WHITE}{tags['TPE1'].text[0]}")
                    else:
                        print(f"Sanatçı: {tags['TPE1'].text[0]}")
                if 'TIT2' in tags:  # Başlık
                    if COLORAMA_AVAILABLE:
                        print(f"{Fore.CYAN}Başlık: {Fore.WHITE}{tags['TIT2'].text[0]}")
                    else:
                        print(f"Başlık: {tags['TIT2'].text[0]}")
                if 'TALB' in tags:  # Albüm
                    if COLORAMA_AVAILABLE:
                        print(f"{Fore.CYAN}Albüm: {Fore.WHITE}{tags['TALB'].text[0]}")
                    else:
                        print(f"Albüm: {tags['TALB'].text[0]}")
            
            # Diğer formatlar için
            if hasattr(audio, 'info'):
                info = {
                    'Süre': f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d}",
                }
                
                if hasattr(audio.info, 'bitrate'):
                    info['Bit hızı'] = f"{audio.info.bitrate // 1000} kbps"
                    
                if hasattr(audio.info, 'sample_rate'):
                    info['Örnekleme hızı'] = f"{audio.info.sample_rate} Hz"
                
                for key, value in info.items():
                    if COLORAMA_AVAILABLE:
                        print(f"{Fore.CYAN}{key}: {Fore.WHITE}{value}")
                    else:
                        print(f"{key}: {value}")
                    
            if COLORAMA_AVAILABLE:
                print(f"{Fore.YELLOW}==================================={Style.RESET_ALL}")
            else:
                print("===================================")
        except Exception as e:
            self.print_error(f"Meta veriler alınamadı: {e}")

    def set_music_dir(self, directory):
        """Müzik dizinini değiştirir"""
        if os.path.isdir(directory):
            self.music_dir = directory
            self.refresh_playlist()
            return True
        else:
            self.print_error(f"{directory} geçerli bir dizin değil.")
            return False

    def show_help(self):
        """Komutları gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}==== Konsol Müzik Oynatıcısı Komutları ===={Style.RESET_ALL}")
            print(f"{Fore.GREEN}play, p      {Fore.WHITE}: Şarkıyı oynat")
            print(f"{Fore.GREEN}stop, s      {Fore.WHITE}: Şarkıyı durdur")
            print(f"{Fore.GREEN}next, n      {Fore.WHITE}: Sonraki şarkı")
            print(f"{Fore.GREEN}prev         {Fore.WHITE}: Önceki şarkı")
            print(f"{Fore.GREEN}vol+, v+     {Fore.WHITE}: Sesi artır")
            print(f"{Fore.GREEN}vol-, v-     {Fore.WHITE}: Sesi azalt")
            print(f"{Fore.GREEN}vol [0-100]  {Fore.WHITE}: Ses seviyesini ayarla")
            print(f"{Fore.GREEN}shuffle      {Fore.WHITE}: Çalma listesini karıştır")
            print(f"{Fore.GREEN}repeat, r    {Fore.WHITE}: Tekrar modunu değiştir")
            print(f"{Fore.GREEN}search [metin]{Fore.WHITE}: Şarkı ara")
            print(f"{Fore.GREEN}info, i      {Fore.WHITE}: Çalan şarkı bilgilerini göster")
            print(f"{Fore.GREEN}list, l      {Fore.WHITE}: Çalma listesini göster")
            print(f"{Fore.GREEN}dir [yol]    {Fore.WHITE}: Müzik dizinini değiştir")
            print(f"{Fore.GREEN}refresh      {Fore.WHITE}: Çalma listesini yenile")
            print(f"{Fore.GREEN}current, c   {Fore.WHITE}: Çalan şarkıyı göster")
            print(f"{Fore.GREEN}help, h      {Fore.WHITE}: Bu yardım menüsü")
            print(f"{Fore.GREEN}quit, q      {Fore.WHITE}: Çıkış")
            print(f"{Fore.CYAN}======================================{Style.RESET_ALL}\n")
        else:
            print("\n==== Konsol Müzik Oynatıcısı Komutları ====")
            print("play, p      : Şarkıyı oynat")
            print("stop, s      : Şarkıyı durdur")
            print("next, n      : Sonraki şarkı")
            print("prev         : Önceki şarkı")
            print("vol+, v+     : Sesi artır")
            print("vol-, v-     : Sesi azalt")
            print("vol [0-100]  : Ses seviyesini ayarla")
            print("shuffle      : Çalma listesini karıştır")
            print("repeat, r    : Tekrar modunu değiştir")
            print("search [metin]: Şarkı ara")
            print("info, i      : Çalan şarkı bilgilerini göster")
            print("list, l      : Çalma listesini göster")
            print("dir [yol]    : Müzik dizinini değiştir")
            print("refresh      : Çalma listesini yenile")
            print("current, c   : Çalan şarkıyı göster")
            print("help, h      : Bu yardım menüsü")
            print("quit, q      : Çıkış")
            print("======================================\n")

    def show_playlist(self):
        """Çalma listesini gösterir"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}==== Çalma Listesi ===={Style.RESET_ALL}")
        else:
            print("\n==== Çalma Listesi ====")
            
        if not self.playlist:
            print("Çalma listesi boş")
        else:
            for i, song in enumerate(self.playlist):
                if i == self.current_song_index:
                    if COLORAMA_AVAILABLE:
                        prefix = f"{Fore.GREEN}► "
                    else:
                        prefix = "► "
                else:
                    prefix = "  "
                    
                if COLORAMA_AVAILABLE:
                    print(f"{prefix}{i+1}. {Fore.WHITE}{os.path.basename(song)}")
                else:
                    print(f"{prefix}{i+1}. {os.path.basename(song)}")
                    
        if COLORAMA_AVAILABLE:
            print(f"{Fore.CYAN}====================={Style.RESET_ALL}\n")
        else:
            print("=====================\n")


def main():
    player = SimpleMusicPlayer()
    
    print("Komutları görmek için 'help' veya 'h' yazın.")
    
    # Ana döngü
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command in ["play", "p"]:
                player.play()
            
            elif command in ["stop", "s"]:
                player.stop()
            
            elif command in ["next", "n"]:
                player.next_song()
                if player.playing:
                    player.play()
            
            elif command == "prev":
                player.prev_song()
                if player.playing:
                    player.play()
            
            elif command in ["vol+", "v+"]:
                player.volume_up()
            
            elif command in ["vol-", "v-"]:
                player.volume_down()
                
            elif command.startswith("vol "):
                try:
                    volume = int(command[4:])
                    player.set_volume(volume)
                except ValueError:
                    player.print_error("Geçersiz ses seviyesi. 0-100 arasında bir değer girin.")
            
            elif command == "shuffle":
                player.shuffle()
                
            elif command in ["repeat", "r"]:
                player.toggle_repeat_mode()
                
            elif command.startswith("search "):
                query = command[7:].strip()
                if query:
                    player.search_song(query)
                else:
                    player.print_warning("Arama sorgusu giriniz.")
            
            elif command in ["info", "i"]:
                player.show_song_info()
            
            elif command in ["list", "l"]:
                player.show_playlist()
            
            elif command.startswith("dir "):
                new_dir = command[4:].strip()
                if new_dir.startswith("~"):
                    new_dir = os.path.expanduser(new_dir)
                player.set_music_dir(new_dir)
            
            elif command in ["refresh"]:
                player.refresh_playlist()
            
            elif command in ["current", "c"]:
                status = "çalıyor" if player.playing else "durduruldu"
                player.print_info(f"Şarkı: {player.get_current_song_name()}")
                player.print_info(f"Durum: {status}")
                player.print_info(f"Ses seviyesi: %{player.volume}")
            
            elif command in ["help", "h"]:
                player.show_help()
            
            elif command in ["quit", "q", "exit"]:
                print("Çıkış yapılıyor...")
                player.stop()
                player.stop_player_checker()
                sys.exit(0)
            
            else:
                player.print_warning("Bilinmeyen komut. Yardım için 'help' yazın.")
                
        except KeyboardInterrupt:
            print("\nÇıkış yapmak için 'q' tuşuna basın.")
        except Exception as e:
            player.print_error(f"Hata: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram sonlandırıldı.")
        # Temizleme işlemleri
        try:
            subprocess.run(['killall', 'mpv'], stderr=subprocess.DEVNULL)
        except:
            pass
        sys.exit(0)
