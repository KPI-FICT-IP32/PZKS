====
PZKS
====


Prerequisites
=============

I was too sleepy to use the containers, but this code extremely relies on
graphviz. It also relies on python3.6 features, like template strings.

So you will need to install the following packages:

- ``graphviz``
- ``python3.6``

To install python dependencies, run:

.. code-block::
    
    pip install -r requirements.txt

Running
=======

In order to start the gui, run the following in your terminal

.. code-block::

   python ui.py


There are some example graphs in ``example`` directory.


Extra
=====

As mentioned above, the code relies on graphviz library, all files, that are
being saved are completely compatible with ``dot`` tool, so you may view graphs
using the following commandline.

.. code-block::

   dot example/system_graph.dot | display

Here ``display`` is a part of ``ImageMagick`` package.
