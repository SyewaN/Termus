# Termus - Linux için Basit Konsol Müzik Çalar

![VoidMusic](https://img.shields.io/badge/VoidMusic-v1.0-blue)
![Python](https://img.shields.io/badge/Python-3.6+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Termus, Void Linux için özel olarak geliştirilmiş basit ve kullanışlı bir konsol tabanlı müzik çalardır. MPV üzerine kurulmuştur ve basit, hızlı ve şık bir arayüz sunar.

## Özellikler

- 🎵 MP3, WAV, OGG, FLAC ve M4A formatlarını destekleme
- 🔊 Ses seviyesi kontrolü
- 🔄 Otomatik şarkı değiştirme
- 🔀 Rastgele çalma modu
- 🎚️ Renkli konsol arayüzü
- 📊 Şarkı ilerleme çubuğu
- 📝 ID3 etiketlerini gösterme (sanatçı, albüm, başlık)
- 🔍 Şarkı arama özelliği
- 🔁 Farklı tekrar modları

## Gereksinimler

- Python 3.6+
- MPV medya oynatıcısı
- Playerctl (ilerleme çubuğu için)
- Colorama (renkli arayüz için)
- Mutagen (şarkı etiketleri için)

## Kurulum

```bash
# Gerekli Paketler
mpv playerctl python3 python3-pip

# Python kütüphanelerini yükleyin
pip install colorama mutagen

# Projeyi indirin
git clone https://github.com/kullaniciadiniz/void-music.git
cd termus-music

# Çalıştırma iznini verin
chmod +x voidmusic.py

# Çalıştırın
./voidmusic.py
```

## Kullanım

Program çalıştırıldığında aşağıdaki komutlar kullanılabilir:

| Komut        | Açıklama                                |
|--------------|----------------------------------------|
| play, p      | Şarkıyı oynat                          |
| stop, s      | Şarkıyı durdur                         |
| next, n      | Sonraki şarkı                          |
| prev         | Önceki şarkı                           |
| vol+, v+     | Sesi artır                             |
| vol-, v-     | Sesi azalt                             |
| vol [0-100]  | Ses seviyesini ayarla                  |
| shuffle      | Çalma listesini karıştır               |
| repeat, r    | Tekrar modunu değiştir                 |
| list, l      | Çalma listesini göster                 |
| search [metin] | Şarkı ara                            |
| info, i      | Çalan şarkı bilgilerini göster         |
| dir [yol]    | Müzik dizinini değiştir                |
| refresh      | Çalma listesini yenile                 |
| current, c   | Çalan şarkıyı göster                   |
| help, h      | Yardım menüsü                          |
| quit, q      | Çıkış                                  |

## Ekran Görüntüleri

```
==== VoidMusic Player ====
█████████████████░░░░░░░░░░░░░░░░░░░ 01:45/03:30
► Çalınıyor: Daft Punk - Get Lucky.mp3
Ses: %60 | Mod: Tümünü Tekrarla
==========================
```

## Lisans

Bu proje GNU GENERAL PUBLIC LICENSE lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## Katkıda Bulunma

1. Bu depoyu forklayın
2. Yeni bir dal oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: Açıklama'`)
4. Dalınıza push yapın (`git push origin yeni-ozellik`)
5. Bir Pull Request oluşturun
