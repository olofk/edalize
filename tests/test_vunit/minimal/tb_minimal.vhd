library vunit_lib;
context vunit_lib.vunit_context;

entity tb_minimal is
  generic (runner_cfg : string);
end entity;

architecture tb of tb_minimal is
begin
  main : process
  begin
    test_runner_setup(runner, runner_cfg);
    while test_suite loop

        if run("testcase_1") then
            report "Hello from testcase_1";
        elsif run("testcase_2") then
            report "Hello from testcase_2";
        end if;
      end loop;
    test_runner_cleanup(runner);
  end process;
end architecture;
