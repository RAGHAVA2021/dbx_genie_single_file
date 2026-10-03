from sales_genie.cli import main

raise SystemExit(main(["import-agent", *__import__("sys").argv[1:]]))
