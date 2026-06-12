# CBS-Rota-Optimizasyonu
Bilgisayar Bilimlerinde Coğrafi Bilgi Sistemleri ve Uygulamaları - Afet Sonrası Elektrik Dağıtım Şebekelerinde PostGIS ve Graf Teorisi Tabanlı Dinamik Rota Optimizasyonu

Bu proje; doğal afetler sonrasında elektrik dağıtım şebekelerinde meydana gelen arızalara müdahale edecek ekipler için **PostgreSQL/PostGIS** ve **Graf Teorisi** tabanlı dinamik bir rota optimizasyon modeli sunmaktadır. Geliştirilen algoritma, salt fiziksel mesafeyi minimize etmek yerine, şebeke unsurlarının iletken tiplerini ve afet şiddetini baz alarak riskli hatları cezalandırır.

Önemli Noktalar 

* **Asimetrik Risk Modellemesi:** Havai ve yeraltı hatların afet kırılganlık asimetrisi dinamik maliyet fonksiyonu ile modellenmiştir.
* **Milisaniye Seviyesinde Karar Destek:** RAM tabanlı grafik optimizasyonu sayesinde sadece **14 ms** CPU süresinde güvenli rota üretilir.
* **%85 Güvenli Hat Önceliği:** Geleneksel rotaların aksine, sistem direnci yüksek olan yeraltı hatlarına otonom öncelik verilir.

* Kullanılan Teknolojiler

* **Dil:** Python (v3.12)
* **Veri Tabanı:** PostgreSQL / PostGIS (GiST İndexleme)
* **Graf Teorisi:** NetworkX (Dijkstra Min-Heap Veri Yapısı)
* **Görselleştirme:** Matplotlib
