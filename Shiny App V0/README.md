# Measles map — Shiny app

US map of measles cases by **year** and **MMWR week**, using CDC NNDSS data (dataset x9gk-5huc). The app **calls the CDC Socrata API** directly (no CSV needed). States are shaded by case count for the selected week.

## 1. Set your API token

The app needs a CDC Socrata app token. In R, set it in your environment (e.g. in `~/.Renviron`):

```
SOCRATA_APP_TOKEN=your_token_here
```

Get a token: [data.cdc.gov → Profile → Developer Settings](https://data.cdc.gov/profile/edit/developer_settings). Restart R after editing `.Renviron`.

## 2. Install R packages

In R:

```r
install.packages(c("shiny", "leaflet", "dplyr", "sf", "tigris", "httr", "jsonlite", "scales"))
```

## 3. Run the app

From the project root in R:

```r
shiny::runApp("shiny_app")
```

Or from this folder:

```r
setwd("shiny_app")
shiny::runApp()
```

## 4. Use the app

1. Click **"Load data from CDC API"** to fetch measles data (2022–present).
2. After it loads, choose **Year** and **MMWR Week** in the sidebar.
3. The map shows case counts per state for that week (choropleth).
