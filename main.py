import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from math import log2

class CacheSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cache Simulator")

        self.cache_size = tk.IntVar(value=16)
        self.memory_size = tk.IntVar(value=256)
        self.block_size = tk.IntVar(value=4)
        self.memory_references = tk.StringVar(value="")
        self.cache_mapping = tk.StringVar(value="Direct Mapping")  # Default to Direct Mapping

        self.hits = 0
        self.misses = 0
        self.evictions = 0

        self.create_gui()

    def create_gui(self):
        self.binary_address_label = tk.Label(self, text="")
        self.binary_address_label.grid(row=6, columnspan=2)

        self.bits_label = tk.Label(self, text="")
        self.bits_label.grid(row=7, columnspan=2)

        self.results_label = tk.Label(self, text="")
        self.results_label.grid(row=8, columnspan=2)

        tk.Label(self, text="Cache Size:").grid(row=0, column=0, sticky="w")
        cache_size_entry = tk.Entry(self, textvariable=self.cache_size)
        cache_size_entry.grid(row=0, column=1)

        tk.Label(self, text="Memory Size:").grid(row=1, column=0, sticky="w")
        memory_size_entry = tk.Entry(self, textvariable=self.memory_size)
        memory_size_entry.grid(row=1, column=1)

        tk.Label(self, text="Block Size:").grid(row=2, column=0, sticky="w")
        block_size_entry = tk.Entry(self, textvariable=self.block_size)
        block_size_entry.grid(row=2, column=1)

        tk.Label(self, text="Memory References (comma separated):").grid(row=3, column=0, sticky="w")
        memory_references_entry = tk.Entry(self, textvariable=self.memory_references)
        memory_references_entry.grid(row=3, column=1)

        tk.Label(self, text="Cache Mapping:").grid(row=4, column=0, sticky="w")
        cache_mapping_combobox = ttk.Combobox(self, textvariable=self.cache_mapping, values=["Direct Mapping", "2-Way Set Associative"])
        cache_mapping_combobox.grid(row=4, column=1)

        tk.Button(self, text="Start Simulation", command=self.start_simulation).grid(row=5, columnspan=2)

        self.before_cache_label = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.before_cache_label.grid(row=9, column=0)

        self.after_cache_label = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=40, height=10)
        self.after_cache_label.grid(row=9, column=1)

    def start_simulation(self):
        cache_size = self.cache_size.get()
        memory_size = self.memory_size.get()
        block_size = self.block_size.get()
        memory_references = [int(x.strip()) for x in self.memory_references.get().split(',')]
        cache_mapping = self.cache_mapping.get()

        # Perform Cache Simulation
        if cache_mapping == "Direct Mapping":
            before_cache, after_cache, self.hits, self.misses, self.evictions = self.direct_mapping_simulation(cache_size, memory_size, block_size, memory_references)
        elif cache_mapping == "2-Way Set Associative":
            before_cache, after_cache, self.hits, self.misses, self.evictions = self.two_way_set_associative_simulation(cache_size, memory_size, block_size, memory_references)

        # Display Cache Contents
        before_cache_text = "Before Cache Fill:\n" + "\n".join(before_cache)
        after_cache_text = "After Cache Fill:\n" + "\n".join(after_cache)

        self.before_cache_label.delete('1.0', tk.END)
        self.before_cache_label.insert(tk.END, before_cache_text)

        self.after_cache_label.delete('1.0', tk.END)
        self.after_cache_label.insert(tk.END, after_cache_text)

        # Display Results
        result_text = f"Hits: {self.hits}\nMisses: {self.misses}\nEvictions: {self.evictions}"
        self.results_label.config(text=result_text)

    def direct_mapping_simulation(self, cache_size, memory_size, block_size, memory_references):
        hits, misses, evictions = 0, 0, 0
        num_cache_lines = cache_size // block_size
        cache = [None] * num_cache_lines
        access_order = []  # Track access order of cache blocks

        # Calculate number of index and offset bits
        num_offset_bits = int(log2(block_size))
        num_index_bits = int(log2(num_cache_lines))
        num_tag_bits = int(log2(memory_size)) - num_offset_bits - num_index_bits

        before_cache = ["-"] * num_cache_lines

        results = []

        for reference in memory_references:
            # Convert reference to binary
            binary_address = bin(reference)[2:].zfill(32)

            # Capture cache contents before processing current reference
            before_cache_copy = list(cache)

            # Calculate index, tag, and word offset
            index = (reference // block_size) % num_cache_lines
            tag = reference // (num_cache_lines * block_size)
            word_offset = reference % block_size

            # Check if the block is in the cache
            if cache[index] == tag:
                hits += 1
                results.append((binary_address, "Hit"))
            else:
                if cache[index] is not None:  # Evict the block if the cache line is occupied
                    evictions += 1
                cache[index] = tag
                misses += 1
                results.append((binary_address, "Miss"))

            # Update cache access order
            if index in access_order:
                access_order.remove(index)
            access_order.append(index)

        # Update cache contents after processing current reference
        after_cache = [f"Cache Line {i}: {hex(tag)}" if tag is not None else f"Cache Line {i}: Empty" for i, tag in enumerate(cache)]

        return before_cache, after_cache, hits, misses, evictions

    def two_way_set_associative_simulation(self, cache_size, memory_size, block_size, memory_references):
        hits, misses, evictions = 0, 0, 0
        num_sets = cache_size // (2 * block_size)
        cache = [[None, None] for _ in range(num_sets)]  # Initialize cache as a 2D list
        lru_counters = [[0, 0] for _ in range(num_sets)]  # Initialize LRU counters
        access_order = []  # Track access order of cache blocks

        # Calculate number of index and offset bits
        num_offset_bits = int(log2(block_size))
        num_index_bits = int(log2(num_sets))
        num_tag_bits = int(log2(memory_size)) - num_offset_bits - num_index_bits

        before_cache = ["-"] * num_sets

        results = []

        for reference in memory_references:
            # Convert reference to binary
            binary_address = bin(reference)[2:].zfill(32)

            # Capture cache contents before processing current reference
            before_cache_copy = [list(set_cache) for set_cache in cache]

            # Calculate index, tag, and word offset
            index = (reference // block_size) % num_sets
            tag = reference // (num_sets * block_size)
            word_offset = reference % block_size

            # Check if the block is in the cache
            if tag in cache[index]:
                hits += 1
                results.append((binary_address, "Hit"))
                # Update LRU counters
                access_order.remove(index)
                access_order.append(index)
                for i in range(len(access_order)):
                    lru_counters[access_order[i]] = i
            else:
                if None in cache[index]:  # Check if there's an empty slot
                    empty_slot_index = cache[index].index(None)
                    cache[index][empty_slot_index] = tag
                else:  # If no empty slot, evict the LRU block
                    evictions += 1
                    lru_index = lru_counters[index].index(max(lru_counters[index]))
                    cache[index][lru_index] = tag
                misses += 1
                results.append((binary_address, "Miss"))
                # Update LRU counters
                if index in access_order:
                    access_order.remove(index)
                access_order.append(index)
                for i in range(len(access_order)):
                    lru_counters[access_order[i]] = i

        # Update cache contents after processing current reference
        after_cache = [f"Set {i}: {cache[i]}" for i in range(num_sets)]

        # Display binary address and bits required
        binary_address_text = "\n".join(f"{address} - {result}" for address, result in results)
        bits_text = f"Tag bits: {num_tag_bits}\nIndex bits: {num_index_bits}\nOffset bits: {num_offset_bits}"

        self.binary_address_label.config(text=binary_address_text)
        self.bits_label.config(text=bits_text)

        return before_cache, after_cache, hits, misses, evictions


if __name__ == "__main__":
    app = CacheSimulator()
    app.mainloop()
