import os
import pickle
from operator import itemgetter
import numpy as np
from .config import DATA_DIR
from .tokenizer import Token
from .exceptions import CacheNotFoundError


class Result:
    def __init__(self, **kwargs):
        self.token = Token(**kwargs)
        self.lan = kwargs['lan']
        self._load_cache()
        self._data_to_vector()
        self.percentage, self.word_list = self._bayes_classify()

    @property
    def get_percentage(self):
        return self.percentage

    @property
    def get_word_list(self):
        return self.word_list

    def _data_to_vector(self):
        '''
        Convert input data to word_vector
        '''
        self.word_vec = [0]*len(self._vocab_list)
        for i in self.token.tokenizer:
            if i in self._vocab_list:
                self.word_vec[self._vocab_list.index(i)] += 1

    def _bayes_classify(self):
        '''
        Bayes classify
        '''
        possibility_vector = []
        log_list = []
        for i in self._ps_vector:
            # final_vector: [0, -7.3, 0, 0, -8, ...]
            final_vector = i[0] * self.word_vec
            # word_index: [1, 4]
            word_index = np.nonzero(final_vector)
            non_zero_word = np.array(self._vocab_list)[word_index]
            # non_zero_vector: [-7.3, -8]
            non_zero_vector = final_vector[word_index]
            possibility_vector.append(non_zero_vector)
            log_list.append(sum(final_vector) + i[1])
        possibility_array = np.array(possibility_vector)
        max_val = max(log_list)
        for i, j in enumerate(log_list):
            if j == max_val:
                max_array = possibility_array[i, :]
                left_array = np.delete(possibility_array, i, 0)
                sub_array = np.zeros(max_array.shape)
                for k in left_array:
                    sub_array += max_array - k
                return self._update_category(log_list), \
                    list(zip(non_zero_word, sub_array))

    def _update_category(self, lst):
        out_lst = [[self.CLASSIFY[i], lst[i]] for i in range(len(self.CLASSIFY))]
        sorted_lst = sorted(out_lst, key=itemgetter(1), reverse=True)
        relative_lst = [2**(v-sorted_lst[0][1]) for k, v in sorted_lst]
        percentage_lst = [i/sum(relative_lst) for i in relative_lst]
        return sorted_lst

    def _load_cache(self):
        cache_path = os.path.join(DATA_DIR, 'data/' + self.lan + '/cache/')
        try:
            with open(cache_path + 'vocab_list.cache', 'rb') as f:
                self._vocab_list = pickle.load(f)
            with open(cache_path + 'vector.cache', 'rb') as f:
                self._ps_vector = pickle.load(f)
            with open(cache_path + 'classify.cache', 'rb') as f:
                self.CLASSIFY = pickle.load(f)
        except FileNotFoundError:
            error = (
                'Cache files not found,' +
                'maybe you should train the data first.')
            raise CacheNotFoundError(error)

    @property
    def get_token(self):
        return self.token
