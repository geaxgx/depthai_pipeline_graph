# DepthAI Pipeline Graph [Experimental]

**WARNING! There is more recent version of this tool there: https://github.com/luxonis/depthai_pipeline_graph
<br>You should use the version of Luxonis as some features have been updated or added.**

A tool that dynamically creates graphs of [DepthAI pipelines](https://docs.luxonis.com/projects/api/en/latest/components/pipeline/). 
<br>
I have created this tool to help me in documenting some of my DepthAI repositories, but it is also useful to quickly get some high-level view of existing DepthAI programs without reading the code.
<br> 


<p align="center"> <img  src="media/graph_human_machine_safety.png" alt="Graph of depthai-experiments/gen2-human-machine-safety"></p>

## How it works ?
In the DepthAI context, a pipeline is a collection of nodes and links between them. 
In your code, after defining your pipeline, you usually pass your pipeline to the device, with a call similar to:
```
device.startPipeline(pipeline)
```
or
```
with dai.Device(pipeline) as device:
```
What happens then, is that the pipeline configuration gets serialized to JSON and sent to the OAK device. If the environment variable `DEPTHAI_LEVEL` is set to `debug` before running your code, the content of the JSON config is printed to the console like below:
```
[2022-06-01 16:47:33.721] [debug] Schema dump: {"connections":[{"node1Id":8,"node1Output":"passthroughDepth","node1OutputGroup":"","node2Id":10
,"node2Input":"in","node2InputGroup":""},{"node1Id":8,"node1Output":"out","node1OutputGroup":"","node2Id":9,"node2Input":"in","node2InputGroup":""},{"node1Id":7,"node1Output":"depth","node1OutputGroup":"","node2Id":8,"node2Input":"inputDepth","node2InputGroup":""},{"node1Id":0,"node1Output":"preview","node1OutputGroup":"","node2Id":8,"node2Input":"in","node2InputGroup":""},{"node1Id":0,"node1Output":"preview","node1OutputGroup":"","node2Id":3,"node2Input":"inputImage","node2InputGroup":""}, 
...
```
By analyzing the printed schema dump, it is then possible to retrieve the nodes of the pipeline and their connections. That's exactly what the tool `pipeline_graph` is doing:
* it sets  `DEPTHAI_LEVEL` to `debug`,
* it runs your code,
* it catches the schema dump in the ouput stream of the code (by default the tool then terminates the process running your code),
* it parses the schema dump and creates the corresponding graph using a modified version of the [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt) framework.
<br>




## Install

```
pip install git+https://github.com/geaxgx/depthai_pipeline_graph.git
```
If not already present, the command above will install the python module Qt.py. Qt.py enables you to write software that runs on any of the 4 supported bindings - PySide2, PyQt5, PySide and PyQt4. If none of these binding is installed, you will get an error message when running `pipeline_graph`: 
```
ImportError: No Qt binding were found. 
```
If you don't have a preference for any particular binding, you can just choose to install PySide2:
```
pip install PySide2
```


## Run

Once the installation is done, you have only one command to remember and use: `pipeline_graph`
```
> pipeline_graph -h
usage: pipeline_graph [-h] {run,from_file,load} ...

positional arguments:
  {run,from_file,load}  Action
    run                 Run your depthai program to create the corresponding
                        pipeline graph
    from_file           Create the pipeline graph by parsing a file containing
                        the schema (log file generated with
                        DEPTHAI_LEVEL=debug or Json file generated by
                        pipeline.serializeToJSon())
    load                Load a previously saved pipeline graph

optional arguments:
  -h, --help            show this help message and exit
```

There are 3 actions/modes available: `run`, `from_file` and `load`

### 1) pipeline_graph run


```
> pipeline_graph run -h
usage: pipeline_graph run [-h] [-dnk] [-var] [-p PIPELINE_NAME] [-v] command

positional arguments:
  command               The command with its arguments between ' or " (ex:
                        python script.py -i file)

optional arguments:
  -h, --help            show this help message and exit
  -dnk, --do_not_kill   Don't terminate the command when the schema string has
                        been retrieved
  -var, --use_variable_names
                        Use the variable names from the python code to name
                        the graph nodes
  -p PIPELINE_NAME, --pipeline_name PIPELINE_NAME
                        Name of the pipeline variable in the python code
                        (default=pipeline)
  -v, --verbose         Show on the console the command output

```

As an example, let's say that the usual command to run your program is:
```
python main.py -cam
```
To build the corresponding pipeline graph, you simply use the following command (the quotes are important):
```
pipeline_graph run "python main.py -cam"
```
Note that as soon as the `pipeline_graph` program has catched the schema dump, your program is forced to be terminated. It means that your program will possibly not have time to display any windows (if it is something it is normally doing).
If you prefer to let your program continue its normal job, use the "-dnk" or "--do_not_kill" argument:
```
pipeline_graph run "python main.py -cam" -dnk
```
Note how the `pipeline_graph` own arguments are placed outside the pair of quotes, whereas your program arguments are inside. 
<br>When using the `-dnk` option, the pipeline graph is displayed only after you quit your program.



**Nodes**

By default, the node name in the grapth is its type (ColorCamera, ImageManip, NeuralNetwork,...) plus a index between parenthesis that corresponds to the order of creation of the node in the pipeline. For example, if the rgb camera is the first node you create, its name will be `"ColorCamera (0)"`.
<br>
When you have a lot of nodes of the same type, the index is not very helpful to distinguish between nodes. You can then used the `-var` or `--use_variable_names` argument to get a more meaningful name: the index number is replaced by the node variable name used in your code. The tool must know the variable name of the pipeline. "pipeline" is the default. Use the `-p` or `--pipeline_name` argument to specify another name.

<p align="center"> <img  src="media/pipeline_graph_naming.png" alt="Graph of the Human Machine Safety demo"></p>

Note that when using this option, `pipeline_graph` will significantly run slower to build the graph (it relies on the python module "trace").

**Ports**

For the input ports, the color represents the blocking state of the port (orange for blocking, green for non-blocking), and the number between [] corresponds to the queue size.

<p align="center"> <img  src="media/ports.png" alt="Graph of the Human Machine Safety demo"></p>
<br>
Once the graph is displayed, a few operations are possible.
You will probably reorganize the nodes by moving them if you are not satisfied with the proposed auto-layout. You can rename a node by directly double-clicking its name. If you double-click in a node (apart the name zone), a window opens which lets you change the node color and its name.
By right-clicking in the graph, a menu appears: you can save your graph in a json file, load a previously save graph or do a few other self-explanatory operations.<br>
<br>

### 2) pipeline_graph from_file
Use this command when the "pipeline_graph run" method fails (for instance, if your application is executed as a subprocess) or you don't have access to the application code (so you cannot run it) but the owner of the code send you a log file containing an execution trace.<br>
Two type of files can be parsed by this command:
* a log file generated by setting the environment variable `DEPTHAI_LEVEL` to `debug`, then running the code and saving the standard output: the tool will parse the log file exactly like it does with the "pipeline_graph run" method, looking for the "Schema dump:" string;
* a Json file generated by a call to [pipeline.serializeToJson()](https://docs.luxonis.com/projects/api/en/latest/references/python/#depthai.Pipeline.serializeToJson).

```
> pipeline_graph from_file -h
usage: pipeline_graph from_file [-h] schema_file

positional arguments:
  schema_file  Path of the file containing the schema

optional arguments:
  -h, --help   show this help message and exit

```

### 3) pipeline_graph load
Use this command to open and edit a previously saved pipeline graph.

```
> pipeline_graph load -h
usage: pipeline_graph load [-h] json_file

positional arguments:
  json_file   Path of the .json file

optional arguments:
  -h, --help  show this help message and exit

```

## Credits
* [NodeGraphQt](https://github.com/jchanvfx/NodeGraphQt) by jchanvfx.
