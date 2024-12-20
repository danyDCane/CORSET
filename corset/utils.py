import json
import os
import pickle as pkl
import tempfile
import numpy as np
import mlflow

from os.path import join
from scipy import sparse as sp
from itertools import chain, combinations

pjoin = join


def flatten(stuff):
    """flatten an array"""
    return np.asarray(stuff).flatten()


def support_size(Y: sp.csc_matrix, ids):
    """return number of rows that have all columns specified by ids > 0, assuming Y is a 0/1 matrix"""
    matches_flag = flatten(Y[:, list(ids)].sum(axis=1)) == len(ids)
    return matches_flag.sum()


def get_tempdir(prefix=None, suffix=None, dir=None):
    if dir is not None:
        makedir(dir, usedir=False)
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=dir)


def makedir(d, usedir=True):
    if usedir:
        d = os.path.dirname(d)

    if not os.path.exists(d):
        os.makedirs(d)


def save_pickle(obj, path):
    return pkl.dump(obj, open(path, 'wb'))

def save_file(string, path):
    with open(path, 'w') as f:
        f.write(string)
        
def load_pickle(path):
    return pkl.load(open(path, 'rb'))


def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=4)


def _ensure_is_csrmatrix(m):
    if not isinstance(m, sp.csr_matrix):
        m = m.tocsr()
    return m


def convert_matrix_to_sets(m):
    """given a binary sparse matrix, return a list of sets, each of which is the non-zero indices of the ith row"""
    m = _ensure_is_csrmatrix(m)
    return [set(m[i, :].nonzero()[1]) for i in range(m.shape[0])]


# def convert_matrix_to_sets_v2(m):
#     """
#     improved version of `convert_matrix_to_sets` using `indices` and `indptr`
#     """
#     m = _ensure_is_csrmatrix(m)
#     indices, indptr = m.indices, m.indptr
#     ret = []
#     for i in range(m.shape[0]):
#         ret.append(set(indices[indptr[i]:indptr[i+1]]))
#     return ret

def convert_matrix_to_sets_v2(m):
    m = _ensure_is_csrmatrix(m)  
    indices, indptr = m.indices, m.indptr
    #法一：不使用append
    ret = [set(indices[indptr[i]:indptr[i + 1]]) for i in range(m.shape[0])]
    #法二：直接使用 np.split 將 indices 按 indptr 分割，這樣可以一次性生成所有行的索引片段，避免逐行操作。
    # ret = [set(row) for row in np.split(indices, indptr[1:-1])]
    return ret

def convert_matrix_to_sets_v4(m):
    """
    利用 csr_matrix.nonzero() 批量提取非零索引，按行分組
    使用稀疏矩陣批量提取非零索引
    """
    m = _ensure_is_csrmatrix(m)  
    #indices, indptr = m.indices, m.indptr
    row_indices, col_indices = m.nonzero()  #獲得所有非零元素的行、列索引，減少多次訪問矩陣的開銷。
    ret = [set() for _ in range(m.shape[0])]  #預先創建包含集合的列表
    # 將每個列索引加入到對應的行集合中，比逐行構建集合更有效。
    for row, col in zip(row_indices, col_indices):
        ret[row].add(col)
    return ret

def convert_matrix_to_sets_v5(m):
    """
    直接生成一個多維二元稀疏矩陣，指示每行非零元素的位置
    不需要轉換為列表或集合，直接在稀疏矩陣內部表示行索引
    保持了矩陣的稀疏特性，適合大規模矩陣的運算。
    """
    m = _ensure_is_csrmatrix(m)
    # 將矩陣中的所有非零元素轉為1，表示二元狀態
    ret = (m != 0).astype(int)
    return ret

def filter_rows_with_no_labels(X: sp.csr_matrix, Y: sp.csr_matrix):
    mask = (flatten(Y.sum(axis=1)) > 0)
    return X[mask], Y[mask]


# @jit(nopython=True)
def array_product(arr):
    res = 1.
    for e in arr:
        res *= e
    return res


def counter2proba(counter):
    total = sum(counter.values())
    proba = {}
    for k, freq in counter.items():
        proba[k] = freq / total
    return proba

# @profile
def conjunctive_collapse(matrix: sp.csc_matrix, cols: tuple):
    """select columns of mat indicated by cols
    evaluate each row conjunctively
    """
    # TODO: simply iterate and add up the columns
    m_sub = matrix[:, cols]
    m_sub_csr = m_sub.tocsr()
    return flatten(m_sub_csr.sum(axis=1)) == len(cols)


# def conjunctive_collapse_v2(matrix: sp.csc_matrix, cols: tuple):
#     """implementation of conjunctive_collapse using set operation
#     """
#     assert isinstance(matrix, sp.csc_matrix)

#     assert len(cols) > 0
#     indices, indptr = matrix.indices, matrix.indptr

#     shared_rows = []

#     list_of_sets = [set(indices[indptr[i]:indptr[i+1]]) for i in cols]
#     list_of_sets = list(sorted(list_of_sets, key=len))
#     smallest_set = list_of_sets[0]

#     for el in smallest_set:
#         # check if el is in every set
#         # if so, add it to shared_rows
#         success = True
#         for a_set in list_of_sets[1:]:
#             if el not in a_set:
#                 # no need to add this element
#                 success = False
#                 break
#         if success:
#             shared_rows.append(el)

#     ret = np.zeros(matrix.shape[0], dtype=bool)
#     ret[shared_rows] = 1
#     return ret

def conjunctive_collapse_v2(matrix: sp.csc_matrix, cols: tuple):
    """更高效地使用集合交集運算來找出共同行"""
    assert isinstance(matrix, sp.csc_matrix)
    assert len(cols) > 0
    
    indices, indptr = matrix.indices, matrix.indptr
    
    # 直接使用交集來計算共同行
    list_of_sets = [set(indices[indptr[i]:indptr[i + 1]]) for i in cols]
    shared_rows = set.intersection(*list_of_sets)
    
    # 建立布林陣列
    ret = np.zeros(matrix.shape[0], dtype=bool)
    ret[list(shared_rows)] = 1
    return ret

def binary_vector_to_set(vect):
    """extract indices of non-zero entries and put into a set"""
    return set((vect > 0).nonzero()[0])


def convert_sets_to_matrix(sets, L: int):
    """
    input: 
    sets: a list of sets, e.g., a list of label sets
    L: size of universe where the sets reside

    output: the corresponding sparse matrix in csr_matrix format
    """
    N = len(sets)
    m = sp.lil_matrix((N, L), dtype=bool)
    for i in range(N):
        for j in sets[i]:
            m[i, j] = 1
    return m.tocsr()

def csr_matrix_equal(m1, m2):
    """
    test whether two csr_matrix are equal
    """
    return (m1 != m2).nnz == 0


def create_experiment_if_needed(name):
    exp = mlflow.get_experiment_by_name(name)
    if exp is None:
        exp_id = mlflow.create_experiment(name)
        exp = mlflow.get_experiment_by_name(exp_id)
    return exp


def get_experiment_id_by_name(name):
    exp = create_experiment_if_needed(name)
    return exp.experiment_id


def draw_bernoulli_elementwise(S, exclude_empty=True):
    """draw a subset from a set S, where the probability of each element being drawn in s is 0.5
    further, empty set may be excluded
    """
    def sample_once():
        res = set()
        for el in S:
            if np.random.rand() < 0.5:
                res.add(el)
        return res

    if exclude_empty:
        while True:
            res = sample_once()
            if len(res) > 0:
                break
    else:
        res = sample_once()
    return res

def powerset(iterable, exclude_empty=True):
    """powerset([1,2,3]) --> (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)

    excluding empty set
    """
    start = (1 if exclude_empty else 0)

    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(start, len(s)+1))

