from sales_genie.cli import main

raise SystemExit(main(["run-smoke-tests", *__import__("sys").argv[1:]]))
