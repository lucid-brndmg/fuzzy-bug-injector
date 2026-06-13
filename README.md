# Fuzzy Bug Injector

**Based on [nwyin/edit-bench](https://github.com/nwyin/edit-bench)**

A set of regex-based bug injection strategies. Supports applying multiple mutations to a single file. Can be used for testing compilers/static analyzers/LLMs. 

Usage example:
```sh
python generate.py --dataset example/sample_dataset.json --lang rust --mutation-modules mutations/ --mutation-list example/semantic-mutations.txt
```