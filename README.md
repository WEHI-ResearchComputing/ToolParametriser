# Tool Parametriser
A tool to make benchmarking and parametrising HPC tools easier and streamlined.

To run a test
```
./run.py -c <configfile> -R run
```
Test config file examples are found in `examples`
* MQ `configMQ.toml`
* Diann `configDiaNN_lib.toml` and `configDiaNN_libfree.toml`
* bwa `configbwa.toml`

To collect test results, use a cutdown version of config such as `examples\config.toml`
```
./run.py -c <configfile> -R analyse
```

