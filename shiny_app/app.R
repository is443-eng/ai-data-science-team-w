#
# Measles cases by week and year — US map (Shiny + Leaflet)
# Fetches data from CDC Socrata API (no CSV needed).
# Token: .env in project root (same as Python) or .Renviron.
#

library(shiny)
library(leaflet)
library(dplyr)
library(sf)
library(tigris)
library(httr)
library(jsonlite)

if (!requireNamespace("scales", quietly = TRUE)) install.packages("scales", repos = "https://cloud.r-project.org")
library(scales)

# ---- Load .env from project root (same file as Python scripts) ----
# Tries .env and ../.env so it works whether run from project root or shiny_app/
load_dotenv_if_present <- function() {
  for (path in c(".env", "../.env")) {
    if (file.exists(path)) {
      lines <- readLines(path, warn = FALSE)
      for (line in lines) {
        line <- trimws(line)
        if (line == "" || substr(line, 1L, 1L) == "#") next
        idx <- regexpr("=", line, fixed = TRUE)
        if (idx < 1) next
        key <- trimws(substr(line, 1L, idx - 1L))
        val <- trimws(substr(line, idx + 1L, nchar(line)))
        if (nchar(key) > 0 && key == "SOCRATA_APP_TOKEN" && nchar(val) > 0) {
          val <- sub("^['\"]", "", sub("['\"]$", "", val))
          Sys.setenv(SOCRATA_APP_TOKEN = val)
          break
        }
      }
      break
    }
  }
}
load_dotenv_if_present()

# ---- State name: NNDSS "states" -> tigris "NAME" ----
nndss_to_tigris_name <- function(x) {
  out <- trimws(tools::toTitleCase(tolower(as.character(x))))
  out[out == "District Of Columbia"] <- "District of Columbia"
  out
}

# ---- CDC SODA3 API: fetch measles data ----
CDC_SODA3_URL <- "https://data.cdc.gov/api/v3/views/x9gk-5huc/query.json"
CDC_WHERE <- "lower(label) like '%measles%' AND year >= '2022' AND year <= '2026'"

fetch_measles_from_api <- function(token, limit = 50000L) {
  body <- list(
    query = paste0("SELECT * WHERE ", CDC_WHERE),
    page = list(pageNumber = 1L, pageSize = limit)
  )
  resp <- POST(
    CDC_SODA3_URL,
    body = body,
    encode = "json",
    add_headers(
      "X-App-Token" = token,
      "Content-Type" = "application/json"
    ),
    timeout(60)
  )
  if (!http_error(resp)) {
    parsed <- content(resp, as = "parsed", type = "application/json")
    rows <- if (is.list(parsed) && !is.null(parsed$data)) parsed$data else parsed
    if (is.data.frame(rows)) return(rows)
    if (is.list(rows) && length(rows) > 0) return(dplyr::bind_rows(lapply(rows, as.data.frame)))
  }
  NULL
}

# ---- UI ----
ui <- fluidPage(
  titlePanel("Measles cases by week — US map"),
  sidebarLayout(
    sidebarPanel(
      actionButton("load_btn", "Load data from CDC API", class = "btn-primary"),
      conditionalPanel(
        "input.load_btn > 0",
        selectInput("year", "Year", choices = character(0)),
        sliderInput("week", "MMWR Week", min = 1, max = 53, value = 1, step = 1)
      ),
      p(strong("Data: CDC NNDSS (x9gk-5huc)."), " Token from .env (project root) or .Renviron."),
      width = 3
    ),
    mainPanel(
      uiOutput("message"),
      leafletOutput("map", height = "600px"),
      width = 9
    )
  )
)

# ---- Server ----
server <- function(input, output, session) {
  measles_cache <- reactiveVal(NULL)

  # Load data from API on button click
  observeEvent(input$load_btn, {
    token <- trimws(Sys.getenv("SOCRATA_APP_TOKEN"))
    if (nchar(token) == 0) {
      showNotification("Set SOCRATA_APP_TOKEN in .env (project root) or .Renviron.", type = "error")
      return()
    }
    withProgress(message = "Loading from CDC API...", value = 0, {
      setProgress(0.3)
      raw <- fetch_measles_from_api(token)
      setProgress(0.8)
      if (is.null(raw) || nrow(raw) == 0) {
        showNotification("No data returned. Check token and try again.", type = "error")
        return()
      }
      # Same processing as before: cases from m1, NAME from states
      df <- raw %>%
        mutate(
          cases = suppressWarnings(as.numeric(.data$m1)),
          cases = replace(.data$cases, is.na(.data$cases), 0),
          year = as.character(.data$year),
          week = as.integer(as.numeric(.data$week)),
          NAME = nndss_to_tigris_name(.data$states)
        )
      measles_cache(df)
      setProgress(1)
    })
    showNotification(paste("Loaded", nrow(df), "rows."), type = "message")
  })

  # Populate year choices when data is loaded
  observe({
    md <- measles_cache()
    if (is.null(md) || nrow(md) == 0) return()
    yrs <- sort(unique(md$year), decreasing = TRUE)
    updateSelectInput(session, "year", choices = yrs, selected = yrs[1])
  })

  output$message <- renderUI({
    if (is.null(measles_cache()) || nrow(measles_cache()) == 0) {
      return(div(
        style = "padding: 1em; background: #fff3cd; border-radius: 4px; margin-bottom: 1em;",
        "Click \"Load data from CDC API\" to fetch measles data (token: .env in project root or .Renviron)."
      ))
    }
    NULL
  })

  # US state boundaries (cached in session)
  us_states <- reactive({
    states(cb = TRUE, year = 2022) %>%
      st_transform(4326) %>%
      select(NAME, geometry)
  })

  # Data for selected year/week, one row per state
  measles_week <- reactive({
    md <- measles_cache()
    req(md, nrow(md) > 0, input$year, input$week)
    w <- as.integer(input$week)
    y <- as.character(input$year)
    md %>%
      filter(.data$year == y, .data$week == w) %>%
      group_by(.data$NAME) %>%
      summarise(cases = sum(.data$cases, na.rm = TRUE), .groups = "drop")
  })

  # Join to state polygons (50 states + DC)
  map_data <- reactive({
    req(us_states(), measles_week())
    st <- us_states()
    mw <- measles_week()
    st %>%
      left_join(mw, by = "NAME") %>%
      mutate(cases = replace(.data$cases, is.na(.data$cases), 0))
  })

  output$map <- renderLeaflet({
    md <- map_data()
    req(nrow(md) > 0)
    domain <- md$cases
    bins <- unique(c(0, 1, 2, 5, 10, 25, 50, 100, 500, Inf))
    bins <- sort(bins[bins <= max(domain, 1) | bins == 0])
    if (max(domain) > 100) bins <- c(0, 1, 5, 10, 25, 50, 100, 500, 1000, Inf)
    pal <- colorBin("YlOrRd", domain = domain, bins = bins, na.color = "#f7f7f7")

    leaflet(md) %>%
      addProviderTiles("CartoDB.Positron") %>%
      addPolygons(
        fillColor = ~ pal(cases),
        fillOpacity = 0.7,
        color = "#333",
        weight = 0.5,
        label = ~ paste0(NAME, ": ", cases, " case(s)"),
        highlightOptions = highlightOptions(weight = 2, bringToFront = TRUE)
      ) %>%
      setView(-96, 38, zoom = 4) %>%
      addLegend(pal = pal, values = ~cases, title = "Cases (week)", opacity = 0.9)
  })
}

shinyApp(ui = ui, server = server)
