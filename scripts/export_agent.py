from sales_genie.cli import main

raise SystemExit(main(["export-agent", *__import__("sys").argv[1:]]))
