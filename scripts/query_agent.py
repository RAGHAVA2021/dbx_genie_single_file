from sales_genie.cli import main

raise SystemExit(main(["query-agent", *__import__("sys").argv[1:]]))
