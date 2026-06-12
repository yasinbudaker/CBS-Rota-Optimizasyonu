import os
import math
import networkx as nx
import matplotlib.pyplot as plt
import psycopg2
import psycopg2.extras

class GridResilienceOptimizer:
    """
    Elektrik Dağıtım Şebekeleri için Dinamik Rota Optimizasyon Sınıfı.
    PostGIS ve Graf Teorisi tabanlı hesaplamaları yürütür.
    """

    def __init__(self, use_db=False, db_config=None):
        self.use_db = use_db
        self.db_config = db_config
        self.G = nx.Graph()

    def connect_postgis_and_load_grid(self):
        """SDBMS üzerinden topolojik verileri graf modeline aktarır."""
        if not self.use_db:
            print("[INFO] Veri tabanı bağlantısı kapalı. Ampirik simülasyon moduna geçiliyor...")
            self._generate_simulation_data()
            return

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Node (Düğüm) Çekimi
            cursor.execute('SELECT trafo_id, trafo_kodu, ST_X(geom) as x, ST_Y(geom) as y FROM trafolar;')
            for trafo in cursor.fetchall():
                self.G.add_node(
                    trafo['trafo_id'], 
                    pos=(trafo['x'], trafo['y']), 
                    kodu=trafo['trafo_kodu']
                )

            # Edge (Kenar) Çekimi
            cursor.execute('SELECT source, target, iletken_tipi, uzunluk_m, gecis_maliyeti FROM elektrik_hatlari;')
            for hat in cursor.fetchall():
                self.G.add_edge(
                    hat['source'], hat['target'], 
                    type=hat['iletken_tipi'], 
                    length=hat['uzunluk_m'],
                    base_cost=hat['gecis_maliyeti'], 
                    dynamic_cost=hat['gecis_maliyeti']
                )
            print(f"[SUCCESS] Şebeke Yüklendi: |V|={self.G.number_of_nodes()}, |E|={self.G.number_of_edges()}")
            conn.close()
        except Exception as e:
            print(f"[ERROR] PostGIS bağlantı hatası: {e}. Simülasyona geçiliyor...")
            self._generate_simulation_data()

    def _generate_simulation_data(self):
        """Makalede belirtilen test şebekesini ve özniteliklerini oluşturur."""
        trafo_koordinatlari = {
            1: (32.85, 39.90), 2: (32.86, 39.91), 3: (32.87, 39.90),
            4: (32.85, 39.92), 5: (32.88, 39.91), 6: (32.86, 39.93),
            7: (32.89, 39.92), 8: (32.87, 39.94), 9: (32.88, 39.95), 10: (32.90, 39.94)
        }
        for t_id, coords in trafo_koordinatlari.items():
            self.G.add_node(t_id, pos=coords, kodu=f"TR-{100+t_id}")

        hat_baglantilari = [
            (1, 2, 'Yeraltı'), (1, 4, 'Havai'), (2, 3, 'Yeraltı'), (2, 5, 'Havai'),
            (3, 7, 'Havai'), (4, 6, 'Yeraltı'), (5, 6, 'Yeraltı'), (5, 7, 'Havai'),
            (6, 8, 'Havai'), (7, 10, 'Yeraltı'), (8, 9, 'Yeraltı'), (9, 10, 'Havai')
        ]
        
        for u, v, h_tipi in hat_baglantilari:
            # Öklid mesafesini metreye çevirmek için kaba bir çarpan
            dx, dy = trafo_koordinatlari[u][0] - trafo_koordinatlari[v][0], trafo_koordinatlari[u][1] - trafo_koordinatlari[v][1]
            mesafe = round(math.sqrt(dx**2 + dy**2) * 111000, 2)
            self.G.add_edge(u, v, type=h_tipi, base_cost=mesafe, dynamic_cost=mesafe)

        print(f"[SUCCESS] Simülasyon şebekesi üretildi: |V|={self.G.number_of_nodes()}, |E|={self.G.number_of_edges()}")

    def calculate_dynamic_disaster_costs(self, w_skoru):
        """Denklem 1: C_ij = L_ij * (1 + (A_ij * W)) formülünün koda dökümü."""
        for u, v, data in self.G.edges(data=True):
            # Afet risk katsayısı (A_ij): Havai hatlar (0.8), Yeraltı hatları (0.1)
            a_ij = 0.8 if data['type'] == 'Havai' else 0.1
            
            # Güncellenmiş dinamik ceza maliyeti
            data['dynamic_cost'] = round(data['base_cost'] * (1 + (a_ij * w_skoru)), 2)

        print(f"[INFO] Dinamik ceza matrisi güncellendi (Afet Şiddeti W={w_skoru})")

    def optimize_route(self, baslangic, hedef):
        """Statik vs Dinamik Dijkstra Optimizasyonu Karşılaştırması."""
        # Deterministik Statik Rota (Sadece Mesafe)
        statik_rota = nx.dijkstra_path(self.G, source=baslangic, target=hedef, weight='base_cost')
        statik_mesafe = nx.dijkstra_path_length(self.G, source=baslangic, target=hedef, weight='base_cost')
        
        # Risk Tabanlı Dinamik Rota (Dinamik Maliyet)
        dinamik_rota = nx.dijkstra_path(self.G, source=baslangic, target=hedef, weight='dynamic_cost')
        dinamik_maliyet = nx.dijkstra_path_length(self.G, source=baslangic, target=hedef, weight='dynamic_cost')

        return {
            "statik_rota": statik_rota, 
            "statik_mesafe": round(statik_mesafe, 2),
            "dinamik_rota": dinamik_rota, 
            "dinamik_maliyet": round(dinamik_maliyet, 2)
        }

    def visualize_routes(self, sonuclar, baslangic, hedef):
        """Sonuçları makalenin 'Bulgular' bölümü için harita üzerinde görselleştirir."""
        pos = nx.get_node_attributes(self.G, 'pos')
        plt.figure(figsize=(12, 8))

        # Düğümler ve etiketler
        nx.draw_networkx_nodes(self.G, pos, node_size=600, node_color='lightsteelblue', edgecolors='black')
        nx.draw_networkx_labels(self.G, pos, font_size=10, font_weight='bold')

        # Hat tiplerini renklendir
        havai_hatlar = [(u, v) for u, v, d in self.G.edges(data=True) if d['type'] == 'Havai']
        yeralti_hatlar = [(u, v) for u, v, d in self.G.edges(data=True) if d['type'] == 'Yeraltı']
        
        nx.draw_networkx_edges(self.G, pos, edgelist=havai_hatlar, edge_color='orange', width=2, style='dashed', alpha=0.6, label='Havai Hat')
        nx.draw_networkx_edges(self.G, pos, edgelist=yeralti_hatlar, edge_color='green', width=2, alpha=0.6, label='Yeraltı Hat')

        # Çözüm Rotalarını Çiz
        statik_edges = list(zip(sonuclar['statik_rota'], sonuclar['statik_rota'][1:]))
        nx.draw_networkx_edges(self.G, pos, edgelist=statik_edges, edge_color='red', width=4, alpha=0.8, label='Deterministik Statik Rota')

        dinamik_edges = list(zip(sonuclar['dinamik_rota'], sonuclar['dinamik_rota'][1:]))
        nx.draw_networkx_edges(self.G, pos, edgelist=dinamik_edges, edge_color='blue', width=4, alpha=0.8, label='Önerilen Dinamik Rota')

        plt.title(f"Afet Sonrası Optimizasyon: Düğüm {baslangic} -> Düğüm {hedef}", fontsize=14, fontweight='bold')
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.show()

# --- ÇALIŞTIRMA VE TEST BLOKU ---
if __name__ == "__main__":
    # Sınıfı simülasyon modunda başlat (Veri tabanı olmadan çalışması için use_db=False)
    optimizer = GridResilienceOptimizer(use_db=False)
    optimizer.connect_postgis_and_load_grid()
    
    # Afet şiddetini W=8 olarak belirle (Havai hatların maliyeti fırlayacak)
    optimizer.calculate_dynamic_disaster_costs(w_skoru=8) 
    
    # Merkez Trafodan (1) Ağır Hasarlı Trafoya (10) bakım ekibi gönder
    start_node, target_node = 1, 10
    results = optimizer.optimize_route(start_node, target_node)
    
    print("\n" + "="*50)
    print("ANALİZ SONUÇLARI")
    print("="*50)
    print(f"Statik Rota : {results['statik_rota']} | Kümülatif Mesafe: {results['statik_mesafe']} m")
    print(f"Dinamik Rota: {results['dinamik_rota']} | Dinamik Ceza Skoru: {results['dinamik_maliyet']}")
    print("="*50)

    # Grafiği ekrana çizdir
    optimizer.visualize_routes(results, start_node, target_node)