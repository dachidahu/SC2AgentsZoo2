# DistLadder3
Distributed Ladder system for SC2, version 3. 
Each SC2 agent is encapsulated in a `virtualenv` based folder, as is required by [`SC2AgentsZoo2`](https://git.code.oa.com/scai_group/SC2AgentsZoo2).
Let the agents fight each other and show the results (e.g., win-rate curves, etc.).

In a `simple run`, it exposes:
* raw directory, where you can browse the intermediate files and curves during the evaluation

In a `full run`, it additionally exposes:
* RESTful APIs, by which you can do CRUD operation and view DistLadder3 as a backend

NOTE: Much of the code is borrowed from/based on `DistLadder` version 1 originally written by `jcxiong`.
NOTE: it only runs with Python 3!

# Run with Bare Metal Scripts
TODO See the [doc here](docs/SCRIPTS.md).

# Run with Kubernetes
TODO See the [doc here](docs/K8S.md)

# Dependencies
See `setup.py`, which will be installed when running `pip install -e .`

Other binaries:
* `bayeselo`

