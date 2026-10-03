from sales_genie.cli import main

raise SystemExit(main(["get-agent", *__import__("sys").argv[1:]]))
