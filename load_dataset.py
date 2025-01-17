import numpy as np
import torch
from torch.utils.data.dataset import Dataset
from torch.utils.data.dataloader import DataLoader

import os
if 'DISENTANGLEMENT_LIB_DATA' not in os.environ:
    os.environ.update({'DISENTANGLEMENT_LIB_DATA': os.path.join(os.path.dirname(__file__),
                                                                'scratch',
                                                                'dataset')})

# noinspection PyUnresolvedReferences
from disentanglement_lib.data.ground_truth.named_data import get_named_ground_truth_data


def get_dataset_name():
    """Reads the name of the dataset from the environment variable `AICROWD_DATASET_NAME`."""
    return os.getenv("AICROWD_DATASET_NAME", "cars3d")


class DLIBDataset(Dataset):
    """
    No-bullshit data-loading from Disentanglement Library, but with a few sharp edges.

    Sharp edge:
        Unlike a traditional Pytorch dataset, indexing with _any_ index fetches a random batch.
        What this means is dataset[0] != dataset[0]. Also, you'll need to specify the size
        of the dataset, which defines the length of one training epoch.

        This is done to ensure compatibility with disentanglement_lib.
    """

    def __init__(self, name, seed=0, iterator_len=50000):
        """
        Parameters
        ----------
        name : str
            Name of the dataset use. You may use `get_dataset_name`.
        seed : int
            Random seed.
        iterator_len : int
            Length of the dataset. This defines the length of one training epoch.
        """
        self.name = name
        self.seed = seed
        self.random_state = np.random.RandomState(seed)
        self.iterator_len = iterator_len
        self.dataset = self.load_dataset()

    def load_dataset(self):
        return get_named_ground_truth_data(self.name)

    def __len__(self):
        return self.iterator_len

    def __getitem__(self, item):
        assert item < self.iterator_len
        output = self.dataset.sample_observations(1, random_state=self.random_state)[0]
        # Convert output to CHW from HWC
        return torch.from_numpy(np.moveaxis(output, 2, 0))


def get_dataset(name=None, seed=0, iterator_len=50000):
    """
    Makes a dataset.

    Parameters
    ----------
    name : str
        Name of the dataset use. Defaults to the output of `get_dataset_name`.
    seed : int
        Random seed.
    iterator_len : int
        Length of the dataset. This defines the length of one training epoch.
    Returns
    -------
    DLIBDataset
    """
    name = get_dataset_name() if name is None else name
    return DLIBDataset(name, seed=seed, iterator_len=iterator_len)


def get_loader(name=None, batch_size=32, seed=0, iterator_len=50000, num_workers=0,
               **dataloader_kwargs):
    """
    Makes a dataset and a data-loader.

    Parameters
    ----------
    name : str
        Name of the dataset use. Defaults to the output of `get_dataset_name`.
    batch_size : int
        Batch size.
    seed : int
        Random seed.
    iterator_len : int
        Length of the dataset. This defines the length of one training epoch.
    num_workers : int
        Number of processes to use for multiprocessed data-loading.
    dataloader_kwargs : dict
        Keyword arguments for the data-loader.

    Returns
    -------
    DataLoader
    """
    name = get_dataset_name() if name is None else name
    dlib_dataset = DLIBDataset(name, seed=seed, iterator_len=iterator_len)
    loader = DataLoader(dlib_dataset, batch_size=batch_size, shuffle=True,
                        num_workers=num_workers, **dataloader_kwargs)
    return loader


def test_loader():
    loader = get_loader(num_workers=2)
    for count, b in enumerate(loader):
        print(b.shape)
        # ^ prints `torch.Size([32, 3, 64, 64])` and means that multiprocessing works
        if count > 5:
            break
    print("Success!")


if __name__ == '__main__':
    test_loader()
