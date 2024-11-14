***************
Migration guide
***************

Edalize strives to be backwards-compatible, but as new features are added, some older features become obsolete.
This chapter contains information on how to migrate away from deprecated features and keep up-to-date with the latest best practices.

Migrating from the Tool API to the Flow API
===========================================

Why
---

The original Tool API, where each backend was associated with a specific tool works for many cases, but is less suitable for more advanced flows. The new Flow API builds upon the experience from the Tool API and is designed to support more advanced workflows while keeping the regular flows simple. The Flow API also brings in a number of other features such as cocotb integration for simulators, external tool/flow plugins, selectable frontends, launcher scripts for all tools, etc.

When
----

The Flow API was introduced in Edalize 0.3.0 and since then there has been a gradual shift of porting backends to the Flow API. Starting with Edalize 0.6.x, Tool API backends that already have a Flow API equivalent will be marked as deprecated to encourage users to move over. New features will not be added to existing Tool API backends unless in exceptional circumstances.


How
---

For users that are using Edalize through FuseSoC, the `flow` and `flow_options` tags in the target section replaces the `default_tool` and `tools`. The following examples show how to use the Flow API instead of the Tool API.

.. code-block:: yaml
   :caption: Tool backends with a corresponding flow

       # Old Tool API
       targets:
         fpga:
           default_tool : vivado
           tools:
             vivado:
               part : xc7a35tcpg236-1

       #New Flow API
       targets:
         fpga:
           flow : vivado
           flow_options:
             part : xc7a35tcpg236-1

.. code-block:: yaml
   :caption: Simulators which share a common flow

      # Old Tool API
      targets:
        sim:
          default_tool : icarus
          tools:
            icarus:
              iverilog_options : [-g2012]

      #New Flow API
      targets:
        fpga:
          flow : sim
          flow_options:
            tool : icarus
            iverilog_options : [-g2012]

For users that interface directly with Edalize, the following code snippet shows basic use of the Flow API.

.. literalinclude:: flow.py
  :language: python
