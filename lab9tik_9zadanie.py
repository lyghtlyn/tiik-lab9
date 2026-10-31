import heapq
import math
from collections import Counter
from itertools import count


# --- 9.1 Построение дерева Хаффмана ---
def build_huffman(freq):
    if not freq:
        raise ValueError("Пустой алфавит")
    order = count()
    heap = [(w, next(order), s) for s, w in freq.items() if w > 0]
    if not heap:
        raise ValueError("Все частоты нулевые")
    heapq.heapify(heap)
    while len(heap) > 1:
        w1, _, left = heapq.heappop(heap)
        w2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, next(order), (left, right)))
    tree = heap[0][2]

    codes = {}

    def walk(node, prefix=""):
        if isinstance(node, str):
            codes[node] = prefix or "0"  # 9.5: один символ -> "0"
        else:
            walk(node[0], prefix + "0")
            walk(node[1], prefix + "1")

    walk(tree)
    return tree, codes


# --- 9.2 Характеристики кода ---
def characteristics(freq, codes):
    total = sum(freq.values())
    p = {s: w / total for s, w in freq.items()}
    H = max(0.0, -sum(x * math.log2(x) for x in p.values()))
    L = sum(p[s] * len(codes[s]) for s in p)
    eta = H / L
    return H, L, eta


def print_table(freq, codes):
    print(f"{'Символ':<8}{'Частота':<9}{'Код'}")
    for s in sorted(codes, key=lambda x: (len(codes[x]), codes[x])):
        print(f"{s:<8}{freq[s]:<9}{codes[s]}")
    H, L, eta = characteristics(freq, codes)
    print(f"H(X) = {H:.4f}   L = {L:.4f}   η = {eta:.4f}   R = {1 - eta:.4f}")


# --- 9.3 Кодирование и декодирование ---
def encode(text, codes):
    return "".join(codes[s] for s in text)


def decode(bits, tree):
    if isinstance(tree, str):
        if any(b != "0" for b in bits):
            raise ValueError("Некорректный битовый поток")
        return tree * len(bits)
    result, node = [], tree
    for b in bits:
        if b not in "01":
            raise ValueError("Недопустимый бит")
        node = node[int(b)]
        if isinstance(node, str):
            result.append(node)
            node = tree
    if node is not tree:
        raise ValueError("Неполное кодовое слово")
    return "".join(result)


# --- Прогон: построить, закодировать, декодировать, сравнить ---
def run(text):
    freq = Counter(text)
    tree, codes = build_huffman(freq)
    print_table(freq, codes)
    bits = encode(text, codes)
    print(f"Биты ({len(bits)}): {bits}")
    ok = decode(bits, tree) == text
    print(f"decode(encode(text)) == text: {'OK' if ok else 'ОШИБКА'}")
    assert ok


# --- Проверка обработки некорректных данных ---
def check_errors():
    _, _ = build_huffman({"A": 1, "B": 1})
    tree, _ = build_huffman(Counter("ABCADE"))
    cases = [
        lambda: build_huffman({}),
        lambda: build_huffman({"A": 0}),
        lambda: decode("012", tree),
        lambda: decode("1", tree),
    ]
    for case in cases:
        try:
            case()
        except ValueError:
            continue
        raise AssertionError("ожидалась ошибка")
    print("Некорректные данные (пустой алфавит, нулевые частоты, плохие биты): ошибки перехвачены, OK")


if __name__ == "__main__":
    print("--- 9.4. Сообщение «ABCADE» ---")
    run("ABCADE")
    print("\n--- 9.5. Один уникальный символ «AAAAA» ---")
    run("AAAAA")
    print("\n--- Проверка ошибок ---")
    check_errors()