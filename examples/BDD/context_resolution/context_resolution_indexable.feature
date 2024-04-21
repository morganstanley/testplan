Feature: Indexable mixin example

    Scenario: index into a class which is Indexable

        Given the example indexable is in the context as my_example_indexable

        #simple members
        Then {{my_example_indexable.a}} == 12
        Then {{my_example_indexable.b}} == 13

        # go deeper in list
        Then {{my_example_indexable.l.0}} == 1
        Then {{my_example_indexable.l.1}} == 2
        Then {{my_example_indexable.l.2}} == 5

        # check a dictionary
        Then {{my_example_indexable.d.a}} == 12
        Then {{my_example_indexable.d.b}} == 13
        Then {{my_example_indexable.d.l}} == {{my_example_indexable.l}}