from tqdm import tqdm
from collections import Counter
from ..trie import SetTrie
from ..PRETTI.PRETTI_Trie import PTrie
from ..PRETTI.PRETTI_invertedIndex import InvertedIndex
from ..utils import convert_matrix_to_sets, convert_matrix_to_sets_v2
from logzero import logger

from scipy.sparse import lil_matrix

class NaiveSampleAssignmentMixin:
    def _generate_new_rows(self, Y):
        """map each row to a set of contained clique ids"""
        rows = convert_matrix_to_sets_v2(Y)

        new_rows = []
        for labelset in tqdm(rows):
            new_row = []
            for sample_id, sample in enumerate(self._sample_space):
                if sample.issubset(labelset):
                    new_row.append(sample_id)
            new_rows.append(new_row)
        self.new_rows = new_rows


class TrieSampleAssignmentMixin:
    """for each row in a dataset, find the samples in the reduced sample space using a Trie-based data structure"""

    # @profile
    def _generate_new_rows(self, Y):
        """map each row to a set of contained clique ids"""
        # rows = convert_matrix_to_sets(Y)
        rows = convert_matrix_to_sets_v2(Y)
        new_rows = []

        sample_space = list(
            map(lambda sample: tuple(sorted(sample)), self._sample_space)
        )

        sample2id = dict(map(reversed, enumerate(sample_space)))

        # build the Trie-based index structure
        trie = SetTrie()
        trie.insert_batch(sample_space)

        for labelset in tqdm(rows):
            query = tuple(labelset)
            subsets = trie.search_subsets(query)
            sample_ids = list(map(sample2id.__getitem__, subsets))
            new_rows.append(sample_ids)

        self.new_rows = new_rows  # be sure to set new_rows

class PRETTISampleAssignmentMixin:
    """for each row in a dataset, find the samples in the reduced sample space using a PRETTI data structure"""

    def find_ordering(self):
    	return [x[0] for x in 
    	    Counter([item for sublist in self._sample_space for item in sublist]).most_common()]
    # @profile
    # def _generate_new_rows(self, Y):
    #     """map each row to a set of contained clique ids"""
    #     InvInd = InvertedIndex(Y).Index
    #     ordering = self.find_ordering()
    #     # InvInd = InvertedIndex(Y).build_index() # build inverted index
    #     Trie = PTrie(InvInd, Y.shape[0])  # initialize
    #     # build trie on the fly
    #     for sample_id, sample in enumerate(self._sample_space):
    #         Trie.ProcessRecord(sample_id, sample, ordering)

    #     self.new_rows = Trie.trie_new_rows
    #     logger.info('sample assignment done')
    
    def _generate_new_rows(self, Y):
        """Map each row to a set of contained clique ids."""
        InvInd = InvertedIndex(Y).Index
        ordering = self.find_ordering()

        # 初始化結果為列表，每行存儲受影響的樣本索引
        new_rows_list = [[] for _ in range(Y.shape[0])]

        # 初始化 Trie
        Trie = PTrie(InvInd, Y.shape[0]) 

        # 分批處理樣本空間
        batch_size = 100
        for batch_start in range(0, len(self._sample_space), batch_size):
            batch_samples = self._sample_space[batch_start:batch_start + batch_size]
            for sample_id, sample in enumerate(batch_samples, start=batch_start):
                # 使用 ProcessRecord 方法
                affected_rows = Trie.ProcessRecord(sample_id, sample, ordering)
                for row_id in affected_rows:
                    new_rows_list[row_id].append(sample_id)  # 更新影響行的樣本索引

        # 保存為屬性
        self.new_rows = new_rows_list
        logger.info('Sample assignment done')
