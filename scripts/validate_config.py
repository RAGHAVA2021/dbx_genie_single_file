from sales_genie.cli import main

raise SystemExit(main(["validate-config", *__import__("sys").argv[1:]]))
