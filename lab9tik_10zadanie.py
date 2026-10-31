import heapq
import math
from collections import Counter
from itertools import count

# Условия: пробелы, регистр и знаки препинания учитываются.
# Хранение: канонический код Хаффмана. Заголовок: размер алфавита (2 байта)
# + число бит выравнивания (1 байт); таблица: символ в UTF-8 + длина кода (1 байт).
TEXT = (
    "Сжатие данных - это способ записать одну и ту же информацию меньшим "
    "числом бит. Идея кода Хаффмана проста: символы, которые встречаются "
    "часто, получают короткие кодовые слова, а редкие символы - длинные. "
    "В русском тексте чаще всего попадаются пробел и буквы о, е, а, и, "
    "поэтому именно им достаются самые короткие коды. Чтобы раскодировать "
    "сообщение, получателю нужно знать таблицу кодов, и эта служебная "
    "информация тоже занимает место. Для короткого текста таблица может "
    "съесть всю выгоду, а для длинного её вклад становится почти незаметным."
)


# --- Дерево и коды Хаффмана ---
def build_huffman(freq):
    order = count()
    heap = [(w, next(order), s) for s, w in freq.items() if w > 0]
    heapq.heapify(heap)
    while len(heap) > 1:
        w1, _, left = heapq.heappop(heap)
        w2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, next(order), (left, right)))
    tree = heap[0][2]
    codes = {}

    def walk(node, prefix=""):
        if isinstance(node, str):
            codes[node] = prefix or "0"
        else:
            walk(node[0], prefix + "0")
            walk(node[1], prefix + "1")

    walk(tree)
    return tree, codes


def encode(text, codes):
    return "".join(codes[s] for s in text)


def decode(bits, tree):
    result, node = [], tree
    for b in bits:
        node = node[int(b)]
        if isinstance(node, str):
            result.append(node)
            node = tree
    return "".join(result)


# --- Энтропия, средняя длина ---
def entropy(freq):
    n = sum(freq.values())
    return -sum(w / n * math.log2(w / n) for w in freq.values())


def avg_length(freq, codes):
    n = sum(freq.values())
    return sum(w / n * len(codes[s]) for s, w in freq.items())


# --- Упаковка в байты (канонический код) ---
def canonical_codes(lengths):
    code, prev, codes = 0, None, {}
    for s, l in sorted(lengths.items(), key=lambda kv: (kv[1], kv[0])):
        code = 0 if prev is None else (code + 1) << (l - prev)
        codes[s] = format(code, f"0{l}b")
        prev = l
    return codes


def pack(text, codes):
    lengths = {s: len(c) for s, c in codes.items()}
    bits = encode(text, canonical_codes(lengths))
    pad = (-len(bits)) % 8
    payload = int(bits + "0" * pad, 2).to_bytes((len(bits) + pad) // 8, "big")
    header = len(lengths).to_bytes(2, "big") + bytes([pad])
    table = b"".join(s.encode("utf-8") + bytes([l])
                     for s, l in sorted(lengths.items(), key=lambda kv: (kv[1], kv[0])))
    return header, table, payload, pad


def unpack(blob):
    k, pad, pos, lengths = int.from_bytes(blob[:2], "big"), blob[2], 3, {}
    for _ in range(k):
        n = 1 if blob[pos] < 0x80 else 2
        lengths[blob[pos:pos + n].decode("utf-8")] = blob[pos + n]
        pos += n + 1
    rev = {c: s for s, c in canonical_codes(lengths).items()}
    data = blob[pos:]
    bits = format(int.from_bytes(data, "big"), f"0{len(data) * 8}b")
    bits = bits[:len(bits) - pad]
    out, cur = [], ""
    for b in bits:
        cur += b
        if cur in rev:
            out.append(rev[cur])
            cur = ""
    return "".join(out)


def total_size(text):
    _, codes = build_huffman(Counter(text))
    header, table, payload, _ = pack(text, codes)
    return len(text.encode("utf-8")), len(header) + len(table) + len(payload)


# --- Основная программа ---
def main():
    text, N = TEXT, len(TEXT)
    assert N >= 300
    print("Условия: пробелы, регистр и знаки препинания учитываются")
    print(f"Длина текста: {N} символов")

    print("\n--- 10.1. Частоты и коды ---")
    freq = Counter(text)
    tree, codes = build_huffman(freq)
    print(f"Размер алфавита: {len(freq)}. Десять самых частых символов:")
    print(f"{'Символ':<8}{'Частота':<9}{'Код'}")
    for s, w in freq.most_common(10):
        print(f"{s!r:<8}{w:<9}{codes[s]}")
    bits = encode(text, codes)
    assert decode(bits, tree) == text
    print("decode(encode(text)) == text: OK")

    print("\n--- 10.2. Характеристики ---")
    H, L = entropy(freq), avg_length(freq, codes)
    eta = H / L
    print(f"H(X) = {H:.4f} бит/симв.")
    print(f"L    = {L:.4f} бит/симв.")
    print(f"η    = {eta:.4f} ({eta * 100:.2f} %)")
    print(f"R    = {1 - eta:.4f} ({(1 - eta) * 100:.2f} %)")

    print("\n--- 10.3. Объём данных ---")
    header, table, payload, pad = pack(text, codes)
    utf8 = len(text.encode("utf-8"))
    print(f"UTF-8:           {utf8} байт")
    print(f"Поток Хаффмана:  {len(bits)} бит = {len(payload)} байт")
    print(f"Сжатие данных:   {utf8 / len(payload):.2f}:1 (экономия {(1 - len(payload) / utf8) * 100:.1f} %)")

    print("\n--- 10.4. Служебные данные и выравнивание ---")
    service = len(header) + len(table)
    total = service + len(payload)
    print("Способ хранения: канонический код (символ + длина кода)")
    print(f"Заголовок:       {len(header)} байт")
    print(f"Таблица:         {len(table)} байт")
    print(f"Выравнивание:    +{pad} бит в последнем байте")
    print(f"Итого архив:     {service} + {len(payload)} = {total} байт")
    print(f"Сжатие с таблицей: {utf8 / total:.2f}:1 (экономия {(1 - total / utf8) * 100:.1f} %)")
    assert unpack(header + table + payload) == text
    print("Восстановление текста из байтов архива: OK")

    print("\n--- 10.5. Когда сжатие выгодно ---")
    print(f"{'Символов':<10}{'UTF-8':<8}{'Архив':<8}{'Экономия'}")
    for n in (20, 50, 100, 300, N):
        u, t = total_size(text[:n])
        print(f"{n:<10}{u:<8}{t:<8}{(1 - t / u) * 100:.1f} %")
    print("Вывод:")
    print("1. Выгода растёт с длиной текста: таблица фиксирована, а экономия на данных растёт.")
    print("2. На коротких текстах таблица больше выигрыша, и сжатие невыгодно.")
    print("3. Нужна неравномерность частот: чем меньше H относительно log2(K), тем сильнее сжатие.")
    print("4. Потери на выравнивание (до 7 бит) малы и важны только для очень коротких сообщений.")


if __name__ == "__main__":
    main()