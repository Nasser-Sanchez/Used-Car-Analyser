library(rvest)
library(tidyverse)
library(RSelenium)
library(wdman)
library(netstat)
library(plotly)
library(lme4)
library(bigrquery)
ggplot2::theme_set(theme_bw())


#selenium()

#selenium_object=selenium(retcommand = T,check=F)

#binman::list_versions("chromedriver")


remote_driver=rsDriver(browser = "firefox",
                       #chromever = "136.0.7103.114",
                       verbose = FALSE,
                       port = free_port(),
                       phantomver = NULL
)

remdr=remote_driver$client

#remdr$open

#####

#og link
#link="https://www.autotrader.co.uk/car-search?body-type=Saloon&fuel-type=Petrol&postcode=LU2%207EE&sort=price-desc&zero-to-60=TO_4"
#55k 
#link="https://www.autotrader.co.uk/car-search?body-type=Coupe&fuel-type=Petrol&postcode=nw24ph&price-to=100000&sort=price-asc&zero-to-60=TO_4"
link="https://www.carmax.com/cars/chevrolet/gmc/lexus/lincoln/toyota/4runner/gx-460/lx-570/navigator/navigator-l/suburban-1500/tahoe/yukon/yukon-xl-1500/denali/premier/sr5-premium/trail-premium/trail-special-edition/trd-off-road/trd-off-road-premium/trd-pro/trd-sport?mileage=0-70000&price=50000"
#"https://www.autotrader.co.uk/car-search?body-type=Saloon&fuel-type=Petrol&postcode=nw24ph&price-to=100000&sort=price-asc&zero-to-60=TO_4"
#body_type="Saloon"
#cars=data.frame()

model_names=c("Yukon XL 1500", "Yukon", "Tahoe", "Suburban 1500", "Escalade", "Escalade ESV","4Runner","Grand Highlander",
              "Highlander","Land Cruiser","Sequoia","LX 570", "LX 600", "IS 500","LC 500","RC F","LS 460","LS 500", 
              "Mustang","F150","Challenger","Camaro","Silverado 1500","Expedition","Tundra","Maverick","Ranger",
              "Charger","Durango", "Aviator","Navigator","Navigator L", "Wagoneer","Grand Wagoneer","Expedition Max",
              "Expedition EL","Wagoneer L","GX 460", "GX 550", "TX 350", "Taycan Electric"
              )

#cars_tmp=data.frame()
# function
#####
#function
#Get_Car_Info=function(link){
message("Opening URL")
remdr$navigate(link)

# Cookie acceptance handling
Sys.sleep(2)  # Wait for cookie popup to appear
tryCatch({
  # Find and click "Accept All" or "Accept Cookies" button
  accept_cookies = remdr$findElement(using = "xpath", "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), '同意')]")
  if (!is.null(accept_cookies)) {
    accept_cookies$clickElement()
    Sys.sleep(3)  # Wait for cookies to be accepted
    message("Cookies accepted")
  } else {
    message("No cookie acceptance button found (popup may have auto-dismissed)")
  }
}, error = function(e) {
  message("Cookie popup handling skipped: ", e$message)
})


#html=remdr$getPageSource
#html
message("Scrolling...")
remdr$executeScript("window.scrollTo(0, document.body.scrollHeight);")

see_more=TRUE
while (see_more==TRUE){
  tryCatch({
    results_text=remdr$findElement(using="id", value="see-more--text")
    see_more=TRUE
    # results_text_val=results_text$getElementText()%>%unlist()
    # results_text_string=str_extract(results_text_val,"\\d+\\sof\\s\\d+")
    # first_num_results=str_extract(results_text_string,"\\d+")
    # last_num_results=gsub("\\d+\\sof\\s*","",results_text_string)
    
    results_button=remdr$findElement(using = "id", value="see-more-button")
    results_button$clickElement()
    Sys.sleep(5)
  },
    error=function(cond){
      see_more=FALSE
    }
  )
}

# for (i in 1:200){
#   remdr$executeScript("window.scrollTo(0, document.body.scrollHeight);")
#   Sys.sleep(10)
# }
# message("Getting Cars:")
# 
# 


car_year_make_element=remdr$findElements(using = "css selector", value = ".scct--make-model-info--year-make")
#car_year_make_element$getElementText()
car_year_make=lapply(car_year_make_element,function(x) x$getElementText())%>%unlist()

car_model_trim_element=remdr$findElements(using = "css selector", value = ".scct--make-model-info--model-trim")
car_model_trim=lapply(car_model_trim_element,function(x) x$getElementText())%>%unlist()

price_element=remdr$findElements(using = "css selector", value = ".scct--price-miles-info--price")
price=lapply(price_element,function(x) x$getElementText())%>%unlist()

mileage_element=remdr$findElements(using = "css selector", value = ".scct--sr-only")
mileage=lapply(mileage_element,function(x) x$getElementText())%>%unlist()

#message(paste("Amount of car listings: ",length(car_urls),sep=""))

cars=data.frame(
  year=as.factor(
    str_extract(car_year_make,"\\d+")
  ),
  
  make=as.factor(
    gsub("\\d+\\s*","",car_year_make)
  ),
  model=as.factor(
    str_extract(car_model_trim,str_c(model_names,collapse = "|"))
  ),
  
  trim=as.factor(
    trimws(
      gsub(
        str_c(model_names,collapse = "|"),
        "",
        car_model_trim
      ),
      which = "left"
    )
  ),
  
  mileage=as.numeric(
    gsub(
      "\\s\\w+",
      "",
      gsub("\\,","",mileage)
      )
  ),
  
  price=as.numeric(
    gsub(
      "\\*",
      ""
      ,
      gsub(
        "\\$",
        "",
        gsub(",","",price)
      )
    )
  ),
  platform="carmax",
  year_make_raw=car_year_make,
  model_trim_raw=car_model_trim,
  price_raw=price,
  mileage_raw=mileage
  
                
)%>%
  mutate(
    make_model=paste(as.character(make),as.character(model),sep=" "),
    gm=make %in% c("GMC","Cadillac","Chevrolet"),
    car=paste(make_model,trim,sep=" "),
    car_full=paste(as.character(year),car,sep=" ")
)

# cars=cars%>%mutate(trim=as.factor(
#   gsub(
#     paste(str_c(model_names,collapse = "|"),"\\s?",sep=""),
#     "",
#     car_model_trim
#   )
# ))

#write.csv(cars,file="carmax_USA.csv")

ds=bq_dataset("nas-autotrader-prd","cars")
#bq_table_delete("nas-autotrader-prd.cars.Cars_Test")
#bq_cars=bq_table(ds,"SUV_Trims")
# bq_table_create(
#   bq_cars,
#   fields=cars,
#   friendly_name="Carmax",
#   description="Autotrader Car Data"
# )

#bq_table_upload(bq_cars,cars)
#bq_table_delete("nas-autotrader-prd.cars.Carmax")
bq_table_upload(bq_cars,cars, create_disposition="CREATE_IF_NEEDED", write_disposition="WRITE_APPEND")



#close server
remote_driver$server$stop()
system("taskkill /im java.exe /f")
