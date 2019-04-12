"""TODO."""

import os

from testplan.common.utils.path import default_runpath
from testplan.runners.pools.base import Pool
from testplan import Task

from tests.unit.testplan.runners.pools.tasks.data.sample_tasks import Runnable


def test_pool_basic():
    dirname = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dirname, 'tasks', 'data', 'relative')

    task1 = Task(target=Runnable(5))
    task2 = Task(target='Runnable', module='sample_tasks', path=path,
                 args=(10,), kwargs=dict(multiplier=3))

    assert task1.materialize().run() == 10
    assert task2.materialize().run() == 30

    pool = Pool(name='MyPool', size=4, runpath=default_runpath)
    pool.add(task1, uid=task1.uid())
    pool.add(task2, uid=task2.uid())
    assert pool._input[task1.uid()] is task1
    assert pool._input[task2.uid()] is task2

    with pool:
        while pool.ongoing:
            pass

    assert pool.get(task1.uid()).result ==\
           pool.results[task1.uid()].result == 10
    assert pool.get(task2.uid()).result ==\
           pool.results[task2.uid()].result == 30
