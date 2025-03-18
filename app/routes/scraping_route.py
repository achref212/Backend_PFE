from flask import Blueprint, jsonify
import os

scraping_bp = Blueprint("scraping_bp", __name__)

@scraping_bp.route("/scrape", methods=["GET"])
def run_scraping():
    os.system("cd scraping && scrapy crawl formations -o ../data/formations.json")
    return jsonify({"message": "Scraping terminé ✅"})
