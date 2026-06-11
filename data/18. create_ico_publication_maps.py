#!/usr/bin/env python3
"""Create publication-quality ICO geography maps from Stage 5 GIS datasets."""

from pathlib import Path
import textwrap

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUT = Path("/home/ubuntu/ico_publication_maps")
OUT.mkdir(parents=True, exist_ok=True)

GIS_PATH = Path("/home/ubuntu/source_embedded_stage5/14.gis_mapping_dataset_with_resources.csv")
HUBS_PATH = Path("/home/ubuntu/source_embedded_stage5/13.blockchain_fundraising_hubs_with_resources.csv")
if not GIS_PATH.exists():
    GIS_PATH = Path("/home/ubuntu/upload/14.gis_mapping_dataset.csv")
if not HUBS_PATH.exists():
    HUBS_PATH = Path("/home/ubuntu/upload/13.blockchain_fundraising_hubs.csv")

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

PROJ = ccrs.Robinson()
DATA_CRS = ccrs.PlateCarree()
EXTENT = [-180, 180, -58, 82]


def load_data():
    gis = pd.read_csv(GIS_PATH)
    gis["Latitude"] = pd.to_numeric(gis["Latitude"], errors="coerce")
    gis["Longitude"] = pd.to_numeric(gis["Longitude"], errors="coerce")
    gis["Funds Raised (USD)"] = pd.to_numeric(gis["Funds Raised (USD)"], errors="coerce")
    verified = gis.dropna(subset=["Latitude", "Longitude"]).copy()

    hubs = pd.read_csv(HUBS_PATH)
    hubs["Total Funds Raised (USD)"] = pd.to_numeric(hubs["Total Funds Raised (USD)"], errors="coerce")
    hubs["Number of Projects"] = pd.to_numeric(hubs["Number of Projects"], errors="coerce")
    hubs["Rank"] = pd.to_numeric(hubs["Rank"], errors="coerce")

    location = (verified.groupby(["City", "Country", "Latitude", "Longitude", "Region"], as_index=False)
                .agg(project_count=("Project", "count"),
                     total_funds=("Funds Raised (USD)", "sum"),
                     projects=("Project", lambda x: "; ".join(x))))
    location = location.sort_values("total_funds", ascending=False).reset_index(drop=True)

    hub_geo = hubs.merge(location[["City", "Country", "Latitude", "Longitude", "Region"]], on=["City", "Country"], how="left")
    hub_geo = hub_geo.dropna(subset=["Latitude", "Longitude"]).copy()
    return gis, verified, location, hub_geo


def setup_map(title, subtitle=None):
    fig = plt.figure(figsize=(13.5, 7.4), facecolor="white")
    ax = plt.axes(projection=PROJ)
    ax.set_global()
    ax.set_extent(EXTENT, crs=DATA_CRS)
    ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor="#eef5f9", zorder=0)
    ax.add_feature(cfeature.LAND.with_scale("110m"), facecolor="#f6f4ee", edgecolor="none", zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("110m"), edgecolor="#b8b8b8", linewidth=0.35, zorder=2)
    ax.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor="#777777", linewidth=0.45, zorder=3)
    gl = ax.gridlines(crs=DATA_CRS, draw_labels=False, linewidth=0.35, color="#c7c7c7", alpha=0.65, linestyle="--", zorder=1)
    gl.xlocator = plt.FixedLocator(np.arange(-180, 181, 60))
    gl.ylocator = plt.FixedLocator(np.arange(-60, 91, 30))
    title_text = title if subtitle is None else f"{title}\n{subtitle}"
    ax.set_title(title_text, loc="left", pad=16)
    return fig, ax


def add_common_notes(ax):
    ax.text(0.01, 0.015, "Projection: Robinson | Coordinate system: WGS84 decimal degrees | Data: verified Stage 5 ICO GIS dataset",
            transform=ax.transAxes, fontsize=8.4, color="#4f4f4f", ha="left", va="bottom",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, boxstyle="round,pad=0.25"), zorder=20)
    add_scale_bar(ax)


def add_scale_bar(ax):
    # Visual scale bar; explicitly labelled approximate because scale varies in a world projection.
    x0, y0 = 0.715, 0.045
    width = 0.155
    height = 0.012
    ax.add_patch(Rectangle((x0, y0), width/2, height, transform=ax.transAxes, facecolor="#222222", edgecolor="#222222", zorder=25))
    ax.add_patch(Rectangle((x0 + width/2, y0), width/2, height, transform=ax.transAxes, facecolor="white", edgecolor="#222222", zorder=25))
    ax.text(x0, y0 + 0.018, "0", transform=ax.transAxes, fontsize=8, ha="center", va="bottom", zorder=25)
    ax.text(x0 + width/2, y0 + 0.018, "2,000", transform=ax.transAxes, fontsize=8, ha="center", va="bottom", zorder=25)
    ax.text(x0 + width, y0 + 0.018, "4,000 km", transform=ax.transAxes, fontsize=8, ha="center", va="bottom", zorder=25)
    ax.text(x0 + width/2, y0 - 0.004, "approximate scale", transform=ax.transAxes, fontsize=7.5, ha="center", va="top", color="#555555", zorder=25)


def label_points(ax, df, label_col="City", max_labels=12, color="#202020", size=8.6, offsets=None):
    if offsets is None:
        offsets = {}
    default_offsets = [(5, 4), (5, -8), (-5, 5), (-5, -8), (6, 10), (-6, 10)]
    for i, (_, row) in enumerate(df.head(max_labels).iterrows()):
        label = row[label_col]
        dx, dy = offsets.get(label, default_offsets[i % len(default_offsets)])
        ax.annotate(label, xy=(row["Longitude"], row["Latitude"]), xycoords=DATA_CRS._as_mpl_transform(ax),
                    xytext=(dx, dy), textcoords="offset points", fontsize=size, color=color,
                    ha="left" if dx >= 0 else "right", va="center",
                    path_effects=[pe.withStroke(linewidth=2.6, foreground="white")], zorder=30)


def figure1(verified, location):
    fig, ax = setup_map("Figure 1. Global Distribution of High-Funded ICO Projects",
                        "Verified project headquarters and operational locations in the Top 50 CryptoRank ICO corpus")
    ax.scatter(verified["Longitude"], verified["Latitude"], s=42, transform=DATA_CRS,
               facecolor="#1f78b4", edgecolor="white", linewidth=0.65, alpha=0.88, zorder=10,
               label="Verified ICO project location")

    label_df = location.sort_values(["project_count", "total_funds"], ascending=False).head(12).copy()
    label_points(ax, label_df, label_col="City", max_labels=12, size=8.2)

    legend = ax.legend(loc="lower left", bbox_to_anchor=(0.012, 0.095), frameon=True, framealpha=0.94,
                       facecolor="white", edgecolor="#cccccc", fontsize=9, title="Project locations")
    legend.get_title().set_fontsize(9)
    add_common_notes(ax)
    path = OUT / "figure1_global_distribution_ico_projects.png"
    fig.savefig(path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return path


def size_from_funds(vals, min_size=45, max_size=1850, vmax=None):
    vals = np.asarray(vals, dtype=float)
    if vmax is None:
        vmax = np.nanmax(vals)
    scaled = np.sqrt(vals / vmax)
    return min_size + scaled * (max_size - min_size)


def figure2(location):
    fig, ax = setup_map("Figure 2. Global Fundraising Concentration Map",
                        "Proportional symbols represent total funds raised at verified city-country locations")
    sizes = size_from_funds(location["total_funds"].values)
    ax.scatter(location["Longitude"], location["Latitude"], s=sizes, transform=DATA_CRS,
               facecolor="#d95f02", edgecolor="#6b2d00", linewidth=0.7, alpha=0.62, zorder=10)

    top_labels = location.head(10).copy()
    label_points(ax, top_labels, label_col="City", max_labels=10, size=8.3)

    # Bubble-size legend based on representative fundraising totals.
    amounts = [250_000_000, 1_000_000_000, 4_000_000_000]
    legend_vmax = np.nanmax(location["total_funds"].values)
    handles = [plt.scatter([], [], s=size_from_funds([a], min_size=45, max_size=520, vmax=legend_vmax)[0], facecolor="#d95f02",
                           edgecolor="#6b2d00", alpha=0.62, linewidth=0.7) for a in amounts]
    labels = ["$250 million", "$1 billion", "$4 billion"]
    legend = ax.legend(handles, labels, scatterpoints=1, loc="lower left", bbox_to_anchor=(0.012, 0.095),
                       frameon=True, framealpha=0.94, facecolor="white", edgecolor="#cccccc",
                       labelspacing=1.25, borderpad=1.0, fontsize=9, title="Total funds raised")
    legend.get_title().set_fontsize(9)
    add_common_notes(ax)
    path = OUT / "figure2_global_fundraising_concentration_bubble_map.png"
    fig.savefig(path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return path


def figure3(hub_geo):
    top = hub_geo.sort_values("Total Funds Raised (USD)", ascending=False).head(10).copy()
    fig, ax = setup_map("Figure 3. Leading Blockchain Fundraising Hubs",
                        "Top 10 verified city-country hubs ranked by total ICO fundraising")
    sizes = size_from_funds(top["Total Funds Raised (USD)"].values, min_size=160, max_size=2100)
    ax.scatter(top["Longitude"], top["Latitude"], s=sizes, transform=DATA_CRS,
               facecolor="#2ca25f", edgecolor="#0b4f2a", linewidth=0.85, alpha=0.68, zorder=10)

    # Label each leading hub with rank and city.
    offsets = {
        "Calgary": (6, 7), "Saint John's": (6, -10), "Zug": (8, 8), "Solana Beach": (-7, -10),
        "Vancouver": (-6, 10), "Wilmington": (8, -7), "Taipei": (7, 7), "New York": (8, 8),
        "San Francisco": (-8, -10), "Washington": (8, -11)
    }
    for _, row in top.iterrows():
        label = f"{int(row['Rank'])}. {row['City']}"
        dx, dy = offsets.get(row["City"], (6, 6))
        ax.annotate(label, xy=(row["Longitude"], row["Latitude"]), xycoords=DATA_CRS._as_mpl_transform(ax),
                    xytext=(dx, dy), textcoords="offset points", fontsize=8.5, color="#102b19",
                    ha="left" if dx >= 0 else "right", va="center", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=2.8, foreground="white")], zorder=30)

    amounts = [750_000_000, 1_500_000_000, 4_000_000_000]
    legend_vmax = np.nanmax(top["Total Funds Raised (USD)"].values)
    handles = [plt.scatter([], [], s=size_from_funds([a], min_size=80, max_size=540, vmax=legend_vmax)[0], facecolor="#2ca25f",
                           edgecolor="#0b4f2a", alpha=0.68, linewidth=0.85) for a in amounts]
    labels = ["$750 million", "$1.5 billion", "$4 billion"]
    legend = ax.legend(handles, labels, scatterpoints=1, loc="lower left", bbox_to_anchor=(0.012, 0.095),
                       frameon=True, framealpha=0.94, facecolor="white", edgecolor="#cccccc",
                       labelspacing=1.25, borderpad=1.0, fontsize=9, title="Hub fundraising total")
    legend.get_title().set_fontsize(9)
    add_common_notes(ax)
    path = OUT / "figure3_leading_blockchain_fundraising_hubs.png"
    fig.savefig(path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return path


def write_captions(gis, verified, location, hub_geo, paths):
    total_projects = len(gis)
    verified_projects = len(verified)
    unverified_projects = total_projects - verified_projects
    unique_locations = len(location)
    top_hubs = hub_geo.sort_values("Total Funds Raised (USD)", ascending=False).head(10)
    top_hub_names = ", ".join(top_hubs["City"].tolist())
    total_funds = gis["Funds Raised (USD)"].sum()

    text = f"""# Publication Map Captions and Interpretations\n\n**Dataset note.** The maps use the Stage 5 source-embedded GIS dataset. Of the {total_projects} high-funded ICO projects in the corpus, {verified_projects} have verified mappable coordinates and {unverified_projects} remain unmapped because both country and city were coded as not verified. Fundraising totals across the full corpus equal ${total_funds:,.0f}; proportional-symbol maps use only verified locations.\n\n## Figure 1. Global Distribution of High-Funded ICO Projects\n\n**Caption.** Global distribution of verified high-funded ICO project locations in the Top 50 CryptoRank fundraising corpus. Each point represents one verified project location, plotted from WGS84 decimal-degree coordinates. Labels are shown for selected cities with repeated project activity or high fundraising salience.\n\n**Interpretation.** Figure 1 shows that high-funded ICO entrepreneurship is spatially concentrated rather than evenly distributed across the world economy. The densest pattern appears in North America and Europe, with repeated activity in United States cities, Canadian locations, and Swiss blockchain centers such as Zug and Bern. Asian locations, including Taipei, Singapore, Hong Kong, Jakarta, Bangkok, Phuket, and Tel Aviv, indicate a secondary but geographically extensive corridor across East, Southeast, and West Asia. The Caribbean and offshore jurisdictions also appear as important legal or organizational locations, particularly Antigua and Barbuda, the Cayman Islands, Puerto Rico, and Barbados. Africa and South America are absent from verified locations in this top-funded cohort, suggesting that the largest ICO fundraising events were disproportionately tied to North American, European, Asian, and selected offshore financial geographies.\n\n## Figure 2. Global Fundraising Concentration Map\n\n**Caption.** Proportional-symbol map of total ICO funds raised at verified city-country locations. Bubble size represents the sum of project-level fundraising assigned to each verified location, while overlapping or co-located projects are aggregated at the city level.\n\n**Interpretation.** Figure 2 demonstrates that the financial geography of high-funded ICOs is even more concentrated than the distribution of project counts alone. Calgary dominates the map because Vaulta/EOS accounts for the largest single fundraising total in the dataset, while Saint John’s, Solana Beach, Taipei, Vancouver, Wilmington, Zug, New York, and San Francisco form a second tier of major fundraising locations. The proportional-symbol pattern highlights how a small number of cities and legal domiciles capture a large share of the capital represented in the top-funded ICO cohort. Europe’s role is anchored strongly by Switzerland, especially Zug, whereas North America combines both large single-project locations and multi-project urban clusters. The map therefore reveals a dual geography: operational technology hubs and legal-financial jurisdictions both shape where blockchain fundraising is recorded.\n\n## Figure 3. Leading Blockchain Fundraising Hubs\n\n**Caption.** Leading blockchain fundraising hubs ranked by total verified city-level ICO fundraising. The figure displays the top 10 city-country hubs, with rank labels corresponding to descending total funds raised.\n\n**Interpretation.** Figure 3 isolates the leading urban hubs and shows that top-ranked fundraising is not simply a function of having many projects. Calgary and Saint John’s rank first and second because each is associated with a very large project, while Zug, New York, San Francisco, Vancouver, and Wilmington combine substantial totals with repeated or institutionally significant project activity. The United States supplies several leading hubs, but Switzerland’s Zug remains a major European concentration, reflecting the broader role of Swiss crypto foundations and legal infrastructure. The inclusion of Taipei further demonstrates that Asia’s contribution is significant even within a top-10 hierarchy dominated by North American and European nodes. Overall, the leading-hub map emphasizes the uneven urban hierarchy of blockchain fundraising and the importance of both technology ecosystems and legal headquarters choices.\n\n## Output Files\n\n| Figure | File |\n| --- | --- |\n| Figure 1 | `{paths['fig1']}` |\n| Figure 2 | `{paths['fig2']}` |\n| Figure 3 | `{paths['fig3']}` |\n\n"""
    out = OUT / "ico_map_captions_and_interpretations.md"
    out.write_text(text, encoding="utf-8")
    return out


def main():
    gis, verified, location, hub_geo = load_data()
    paths = {
        "fig1": figure1(verified, location),
        "fig2": figure2(location),
        "fig3": figure3(hub_geo),
    }
    report = write_captions(gis, verified, location, hub_geo, paths)
    print("Generated files:")
    for p in paths.values():
        print(p)
    print(report)


if __name__ == "__main__":
    main()
