import networkx as nx
import matplotlib.pyplot as plt

def draw_topology(devices, connections, output_file='topology.png'):
    """
    Ağ topolojisini çizer ve bir dosyaya kaydeder.

    Args:
        devices (list): Cihazların adlarını veya IP'lerini içeren bir liste.
        connections (list): [(kaynak, hedef)] formatında bağlantılar.
        output_file (str): Kaydedilecek grafik dosyasının adı.
    """
    graph = nx.Graph()

    # Cihazları ekleyin
    for device in devices:
        graph.add_node(device)

    # Bağlantıları ekleyin
    for src, dst in connections:
        graph.add_edge(src, dst)

    # Topolojiyi çiz
    plt.figure(figsize=(10, 7))
    nx.draw(
        graph,
        with_labels=True,
        node_size=3000,
        node_color="skyblue",
        font_size=10,
        font_color="black",
        edge_color="gray",
    )
    plt.savefig(output_file)
    plt.close()

    print(f"Topoloji {output_file} dosyasına kaydedildi.")
