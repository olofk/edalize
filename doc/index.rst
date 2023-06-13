.. image:: https://img.shields.io/github/stars/olofk/edalize?longCache=true&style=flat-square&label=olofk%2Fedalize&logo=github
        :target: https://github.com/olofk/edalize
        :alt: github.com/olofk/edalize

.. image:: https://img.shields.io/badge/Chat-on%20gitter-4db797.svg?longCache=true&style=flat-square&logo=gitter&logoColor=e8ecef
   :alt: Join the chat at https://gitter.im/librecores/edalize
   :target: https://gitter.im/librecores/edalize?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://www.librecores.org/olofk/edalize/badge.svg?style=flat-square
        :target: https://www.librecores.org/olofk/edalize
        :alt: LibreCores

.. image:: https://img.shields.io/pypi/dm/edalize.svg?longCache=true&style=flat-square&logo=PyPI&logoColor=e8ecef&label=PyPI%20downloads
        :target: https://pypi.org/project/edalize/
        :alt: PyPI downloads


Welcome to Edalize's documentation!
===================================

Edalize is an abstraction library that presents a common interface for different EDA tools. It supports many different EDA tools and combinations of tools working together, called flows. A flow could e.g. be an FPGA bitstream flow where one EDA tool is used for synthesis, another one for place & route and a third one to convert the P&R database into an image that can be loaded into the FPGA. Another example could be a simulation flow, where the simulator itself is just one tool, but where a code conversion tool is used to preprocess the input to the simulator, e.g. ghdl to convert VHDL to Verilog for tools that don't handle the former well enough.

The :ref:`Edalize User Guide <ug>` will guide you through how to use the Edalize API to set up and configure EDA flows and use them in your project.

The :ref:`Edalize Developer Guide <dg>` describes how to work with Edalize to fix bugs, improve the current tools and flows or extend with new ones.

.. toctree::
   :caption: User Guide
   :hidden:

   user/index

.. toctree::
   :caption: Developer Guide
   :hidden:

   dev/index

.. toctree::
   :caption: Reference
   :hidden:

   edam/api
   Modules <edalize>
   genindex
   Module Index <py-modindex>
