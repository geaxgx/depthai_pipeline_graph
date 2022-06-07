#!/usr/bin/env python3

def main():
    import subprocess
    from argparse import ArgumentParser
    import os, signal
    import re
    import sys
    from Qt import QtWidgets, QtCore
    from .NodeGraphQt import NodeGraph, BaseNode, PropertiesBinWidget
    from .NodeGraphQt.constants import ViewerEnum
    import json


    node_color = {
        "ColorCamera": (241,148,138),
        "MonoCamera": (243,243,243),
        "ImageManip": (174,214,241),
        "VideoEncoder": (190,190,190),

        "NeuralNetwork": (171,235,198),
        "DetectionNetwork": (171,235,198),
        "MobileNetDetectionNetwork": (171,235,198),
        "MobileNetSpatialDetectionNetwork": (171,235,198),
        "YoloDetectionNetwork": (171,235,198),
        "YoloSpatialDetectionNetwork": (171,235,198),
        "SpatialDetectionNetwork": (171,235,198),

        "SPIIn": (242,215,213), 
        "XLinkIn": (242,215,213),

        "SPIOut": (230,176,170), 
        "XLinkOut": (230,176,170),

        "Script": (249,231,159),

        "StereoDepth": (215,189,226), 
        "SpatialLocationCalculator": (215,189,226),

        "EdgeDetector": (248,196,113), 
        "FeatureTracker": (248,196,113), 
        "ObjectTracker": (248,196,113), 
        "IMU": (248,196,113)
    }

    default_node_color = (190,190,190) # For node types that does not appear in 'node_color'


    class DepthaiNode(BaseNode):
        # unique node identifier.
        __identifier__ = 'dai'

        # initial default node name.
        NODE_NAME = 'Node'

        def __init__(self):
            super(DepthaiNode, self).__init__()

            # create QLineEdit text input widget.
            # self.add_text_input('my_input', 'Text Input', tab='widgets')

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="Action", required=True, dest="action")
    run_parser = subparsers.add_parser("run", help="Run your depthai program to create the corresponding  pipeline graph")
    run_parser.add_argument('command', type=str, 
                help="The command with its arguments between ' or \" (ex: python script.py -i file)")
    run_parser.add_argument("-dnk", "--do_not_kill", action="store_true",
                help="Don't terminate the command when the schema string has been retrieved")
    run_parser.add_argument("-var", "--use_variable_names", action="store_true",
                help="Use the variable names from the python code to name the graph nodes")
    run_parser.add_argument("-p", "--pipeline_name", type=str, default="pipeline",
                help="Name of the pipeline variable in the python code (default=%(default)s)")
    run_parser.add_argument('-v', '--verbose', action="store_true",
                help="Show on the console the command output")

    load_parser = subparsers.add_parser("load", help="Load a previously saved pipeline graph")
    load_parser.add_argument("json_file", 
                help="Path of the .json file")
    args = parser.parse_args()

    # handle SIGINT to make the app terminate on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication(["DepthAI Pipeline Graph"])

    # create node graph controller.
    graph = NodeGraph()
    graph.set_background_color(255,255,255)
    graph.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)

    graph.register_node(DepthaiNode)


    # create a node properties bin widget.
    properties_bin = PropertiesBinWidget(node_graph=graph)
    properties_bin.setWindowFlags(QtCore.Qt.Tool)

    # show the node properties bin widget when a node is double clicked.
    def display_properties_bin(node):
        if not properties_bin.isVisible():
            properties_bin.show()
    # wire function to "node_double_clicked" signal.
    graph.node_double_clicked.connect(display_properties_bin)

        # show the node graph widget.
    graph_widget = graph.widget
    graph_widget.resize(1100, 800)

    if args.action == "load": 
        
        graph_widget.show()
        graph.load_session(args.json_file)
        graph.fit_to_selection()
        graph.set_zoom(-0.9)
        graph.clear_selection()
        graph.clear_undo_stack()

        app.exec_()

    elif args.action == "run":
        os.environ["PYTHONUNBUFFERED"] = "1"
        os.environ["DEPTHAI_LEVEL"] = "debug"
            
        command = args.command.split()
        if args.use_variable_names:
            # If command starts with "python", we remove it
            if "python" in command[0]:
                command.pop(0)

            command = "python -m trace -t ".split() + command
            pipeline_create_re = f'.*:\s*(.*)\s*=\s*{args.pipeline_name}\.create.*'
            node_name = []
        process = subprocess.Popen(command, shell=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        schema_str = None
        record_output = "" # Save the output and print it in case something went wrong
        while True:
            if process.poll() is not None: break
            line = process.stdout.readline()
            record_output += line
            if args.verbose:
                print(line.rstrip('\n'))
            # we are looking for  a line:  ... [debug] Schema dump: {"connections":[{"node1Id":1...
            match = re.match(r'.* Schema dump: (.*)', line)
            if match:
                schema_str = match.group(1)
                print("Pipeline schema retrieved")
                # print(schema_str)
                if not args.do_not_kill:
                    print("Terminating program...")
                    process.terminate()
            elif args.use_variable_names:
                match = re.match(pipeline_create_re, line)
                if match:
                    node_name.append(match.group(1))
        print("Program exited.")

        if schema_str is None:
            if not args.verbose:
                print(record_output)
            print("\nSomething went wrong, the schema could not be extracted")
            exit(1)
        schema = json.loads(schema_str)

        dai_connections = schema['connections']
        dai_nodes = {} # key = id, value = dict with keys 'type', 'blocking', 'queue_size' and 'name' (if args.use_variable_name)
        for n in schema['nodes']:
            dict_n = n[1]
            dai_nodes[dict_n['id']] = {'type': dict_n['name']}
            if args.use_variable_names:
                dai_nodes[dict_n['id']]['name'] = f"{dict_n['name']} - {node_name[dict_n['id']]}"  
            else: 
                dai_nodes[dict_n['id']]['name'] = f"{dict_n['name']} ({dict_n['id']})"
            blocking = {}
            queue_size = {}
            for io in dict_n['ioInfo']:
                dict_io = io[1]
                port_name = dict_io['name']
                blocking[port_name] = dict_io['blocking']
                queue_size[port_name] = dict_io['queueSize']
            dai_nodes[dict_n['id']]['blocking'] = blocking
            dai_nodes[dict_n['id']]['queue_size'] = queue_size

        print("\nNodes (id):\n===========")
        for id in sorted(dai_nodes):
            print(f"{dai_nodes[id]['name']}")


    

        # create the nodes.
        qt_nodes = {}
        for id,node in dai_nodes.items():
            qt_nodes[id] = graph.create_node('dai.DepthaiNode', name=node['name'], color=node_color.get(node['type'], default_node_color), text_color=(0,0,0), push_undo=False)
            
        print("\nConnections:\n============")
        i=0
        for c in dai_connections:
            src_node_id = c["node1Id"]
            src_node = qt_nodes[src_node_id]
            src_port_name = c["node1Output"]
            dst_node_id = c["node2Id"]
            dst_node = qt_nodes[dst_node_id]
            dst_port_name = c["node2Input"]
            dst_port_color = (249,75,0) if dai_nodes[dst_node_id]['blocking'][dst_port_name] else (0,255,0)
            dst_port_label = f"[{dai_nodes[dst_node_id]['queue_size'][dst_port_name]}] {dst_port_name}"
            if not src_port_name in list(src_node.outputs()):
                src_node.add_output(name=src_port_name)
            if not dst_port_label in list(dst_node.inputs()):
                dst_node.add_input(name=dst_port_label, color=dst_port_color, multi_input=True)
            print(i,f"{dai_nodes[src_node_id]['name']}: {src_port_name} -> {dai_nodes[dst_node_id]['name']}: {dst_port_label}")
            # if i == 8:
            #     import pdb; pdb.set_trace()
            src_node.outputs()[src_port_name].connect_to(dst_node.inputs()[dst_port_label], push_undo=False)
            i+=1

        # Lock the ports
        graph.lock_all_ports()

        graph_widget.show()
        # try:
        graph.auto_layout_nodes()
        # except:
        #     print("Auto Layout failed")
        graph.fit_to_selection()
        graph.set_zoom(-0.9)
        graph.clear_selection()
        graph.clear_undo_stack()
        app.exec_()

if __name__ == "__main__":
    main()