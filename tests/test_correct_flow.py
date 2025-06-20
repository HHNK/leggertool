import unittest

# @unittest.skipIf()
from copy import deepcopy
from random import shuffle

from legger.utils.network import Network, Node, Line, Graph


class TestRealNetwork(unittest.TestCase):

    def test_reflow_castricum(self):
        test_sqlite = r'd:\tmp\legger\legger_castricum.sqlite'

        network = Network(test_sqlite)
        network.build_graph_tables()
        start_nodes = network.graph.get_startnodes()
        tree = network.force_direction()
        direction_forced = [line for line in network.graph.lines if line.forced_direction]

        nodes_without_flow = network.re_distribute_flow()
        network.save_network_values()
        lines_without_flow = [line for line in network.graph.lines if line.debiet_modified is None]
        print(len(lines_without_flow))
        a = 1


class TestTheoreticalSimpleNetwork(unittest.TestCase):

    def setUp(self):

        self.nodes = [
            Node(oid=100),
            Node(oid=101),
            Node(oid=102),
            Node(oid=103),
            Node(oid=104),
            Node(oid=105),
        ]

        self.lines = [
            Line(oid=1, startnode_id=101, endnode_id=100, category=1, length=1, debiet_3di=1,
                 debiet_modified=None),
            Line(oid=2, startnode_id=102, endnode_id=101, category=1, length=1, debiet_3di=1,
                 debiet_modified=None),
            Line(oid=3, startnode_id=105, endnode_id=101, category=1, length=1, debiet_3di=1,
                 debiet_modified=None),
            Line(oid=4, startnode_id=103, endnode_id=102, category=1, length=1, debiet_3di=1,
                 debiet_modified=None),
            Line(oid=5, startnode_id=104, endnode_id=103, category=1, length=1, debiet_3di=1,
                 debiet_modified=None),
        ]

    def test_startnrs_one_network(self):
        """ test init network en get start nrs  with one simple network
        network:
              o
              |
              3
              |
              v
        o <-1- o <-2- o <-4- o <-5- o
        """
        network = Network("", graph=Graph(
            lines=self.lines,
            nodes=self.nodes
        ))
        self.assertListEqual([100], sorted([n.id for n in network.get_startnodes()]))
        # reverse have no effect (because also debiet is switched)
        self.lines[4].reverse()
        self.assertListEqual([100], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([104, 105], sorted([n.id for n in network.get_endnodes()]))

        self.assertEqual(103, self.lines[4].outflow_node().id)
        self.assertEqual(104, self.lines[4].inflow_node().id)

    def test_startnrs_two_networks(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              |
              3
              |
              v
        o <-1- o <-2- o <-4- o -5-> o
        """
        # reverse with negative debiet_3di
        lines = deepcopy(self.lines)
        nodes = deepcopy(self.nodes)
        lines[4].debiet_3di = -lines[4].debiet_3di

        network = Network("", graph=Graph(
            lines=lines,
            nodes=nodes
        ))
        self.assertListEqual([100, 104], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([103, 105], sorted([n.id for n in network.get_endnodes()]))

        self.assertEqual(104, lines[4].outflow_node().id)
        self.assertEqual(103, lines[4].inflow_node().id)

        # reverse with inverse direction
        lines = deepcopy(self.lines)
        nodes = deepcopy(self.nodes)

        lines[4].startnode_id, lines[4].endnode_id = lines[4].endnode_id, lines[4].startnode_id

        network = Network("", graph=Graph(
            lines=lines,
            nodes=nodes
        ))

        self.assertListEqual([100, 104], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([103, 105], sorted([n.id for n in network.get_endnodes()]))

        self.assertEqual(104, lines[4].outflow_node().id)
        self.assertEqual(103, lines[4].inflow_node().id)


    def test_startnrs_one_shared_startpoint(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              |
              v
        o --> o <-- o <-- o <-- o
        """
        self.lines[0].debiet_3di = -self.lines[0].debiet_3di

        network = Network("", graph=Graph(
            lines=self.lines,
            nodes=self.nodes
        ))
        self.assertListEqual([101], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([100, 104, 105], sorted([n.id for n in network.get_endnodes()]))

    def test_startnrs_splitted_stream(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              ^
              |
        o <-- o <-- o <-- o <-- o
        """
        self.lines[2].debiet_3di = -self.lines[0].debiet_3di

        network = Network("", graph=Graph(
            lines=self.lines,
            nodes=self.nodes
        ))
        self.assertListEqual([100, 105], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([104], sorted([n.id for n in network.get_endnodes()]))

    def test_startnrs_shuffled_input(self):
        """ test with network of test 'test_startnrs_one_shared_startpoint', with different
        input order (to make sure order of input don't influence results) """
        self.lines[0].debiet_3di = -self.lines[0].debiet_3di

        oid = self.nodes[1].id

        for i in range(0, 5):
            lines = deepcopy(self.lines)
            nodes = deepcopy(self.nodes)
            shuffle(lines)
            shuffle(nodes)

            graph = Graph(lines=lines, nodes=nodes)
            network = Network("", graph=graph)
            self.assertListEqual([101], sorted([n.id for n in network.get_startnodes()]))
            self.assertListEqual([100, 104, 105], sorted([n.id for n in network.get_endnodes()]))


    def test_build_tree_small_bidirectional(self):
        """ test init network en get start nrs  with one simple network
        network:
              o
              |
              v
        o <-- o <-- o <-> o <-- o
        """
        self.lines[2].debiet_3di = None

        network = Network("", graph=Graph(
            lines=self.lines,
            nodes=self.nodes
        ))
        self.assertListEqual([100], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([104, 105], sorted([n.id for n in network.get_endnodes()]))


class TestTheoreticalComplexerNetwork(unittest.TestCase):

    def setUp(self):

        self.nodes = [
            Node(oid=100),
            Node(oid=101),
            Node(oid=102),
            Node(oid=103),
            Node(oid=104),
            Node(oid=105),
            Node(oid=106),
            Node(oid=107),
        ]

        self.lines = [
            Line(oid=9, startnode_id=101, endnode_id=100, category=1, length=1, debiet_3di=2.6,
                 debiet_modified=None),
            Line(oid=1, startnode_id=102, endnode_id=101, category=1, length=1, debiet_3di=1.0,
                 debiet_modified=None),
            Line(oid=2, startnode_id=103, endnode_id=102, category=1, length=1, debiet_3di=0.8,
                 debiet_modified=None),
            Line(oid=3, startnode_id=104, endnode_id=103, category=1, length=1, debiet_3di=1.2,
                 debiet_modified=None),
            Line(oid=4, startnode_id=105, endnode_id=104, category=1, length=1, debiet_3di=1.0,
                 debiet_modified=None),
            Line(oid=5, startnode_id=102, endnode_id=107, category=1, length=1, debiet_3di=0.4,
                 debiet_modified=None),
            Line(oid=6, startnode_id=107, endnode_id=106, category=1, length=1, debiet_3di=1.2,
                 debiet_modified=None),
            Line(oid=7, startnode_id=106, endnode_id=107, category=1, length=1, debiet_3di=1.4,
                 debiet_modified=None),
            Line(oid=8, startnode_id=103, endnode_id=107, category=1, length=1, debiet_3di=0.6,
                 debiet_modified=None),
        ]

    def test_rerouting_of_flow(self):
        """

                  o <-1(6)- o <-----
                  |         ^       2(8)
                  1(7)      1(5)     \
                  v         |         \
        o <-1(9)- o <-2(1)- o <-2(2)- o <-2(3)- o <-2(4)- o

        :return:
        """

        self.lines[2].debiet_3di = None

        network = Network("", graph=Graph(
            lines=self.lines,
            nodes=self.nodes
        ))
        self.assertListEqual([100], sorted([n.id for n in network.get_startnodes()]))
        self.assertListEqual([105], sorted([n.id for n in network.get_endnodes()]))

    # def test_fill_bidirectional_gaps(self):
    #     """
    #
    #               o <-(6)- o <-----
    #               |        ^      (8)
    #              (7)      (5)       \
    #               v        v         v
    #     o <-(9)-> o <-(1)- o <-(2)-> o <-(3)-> o <-(4)- o
    #
    #     :return:
    #     """
    #
    #     one_simple_line_network_for_redistrubution = [
    #         {'id': 1, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 1), (0, 0)]},
    #         {'id': 2, 'debiet': None, 'direction': 3, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 2), (0, 1)]},
    #         {'id': 3, 'debiet': 1.2, 'direction': 1, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 3), (0, 2)]},
    #         {'id': 4, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 4), (0, 3)]},
    #         {'id': 5, 'debiet': None, 'direction': 3, 'categorieoppwaterlichaam': 1, 'geometry': [(1, 1), (0, 1)]},
    #         {'id': 6, 'debiet': 1.2, 'direction': 1, 'categorieoppwaterlichaam': 1, 'geometry': [(1, 1), (1, 0)]},
    #         {'id': 7, 'debiet': 1.4, 'direction': 1, 'categorieoppwaterlichaam': 1, 'geometry': [(1, 0), (0, 0)]},
    #         {'id': 8, 'debiet': None, 'direction': 3, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 2), (1, 1)]},
    #         {'id': 9, 'debiet': None, 'direction': 3, 'categorieoppwaterlichaam': 1, 'geometry': [(0, -1), (0, 0)]},
    #     ]
    #
    #     line_layer, director, distance_properter = self.get_line_layer_and_director(
    #         one_simple_line_network_for_redistrubution)
    #
    #     network = NewNetwork(line_layer, line_layer, director, distance_properter, id_field='id')
    #
    #     # line_layer_updates = network.fill_bidirectional_gaps(bidirectional_islands)

