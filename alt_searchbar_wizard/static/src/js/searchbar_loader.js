// Simple searchbar loader - no widget system
;(function () {
    "use strict"

    // Wait for DOM to be ready
    function initSearchbar() {
        var wrapper = document.getElementById("searchbar_wrapper")
        if (!wrapper) {
            console.log("No searchbar wrapper found")
            return // No searchbar wrapper found
        }

        console.log("Initializing searchbar...")

        // Add a small delay to ensure Odoo is fully loaded
        setTimeout(function () {
            loadSearchbar(wrapper)
        }, 1000)
    }

    function loadSearchbar(wrapper) {
        console.log("Loading searchbar...")

        // First check if searchbar should be shown
        fetch("/alt/searchbar/should_show", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({}),
        })
            .then(function (response) {
                console.log("Should show response:", response)
                return response.json()
            })
            .then(function (shouldShow) {
                console.log("Should show:", shouldShow)
                if (!shouldShow) {
                    // Hide the wrapper if searchbar shouldn't be shown
                    wrapper.style.display = "none"
                    return
                }

                // Load configuration
                return fetch("/alt/searchbar/config", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({}),
                })
            })
            .then(function (response) {
                if (!response) return // Already handled above
                console.log("Config response:", response)
                return response.json()
            })
            .then(function (data) {
                if (!data) return // Already handled above

                console.log("Config data:", data)

                if (data.error) {
                    console.warn("Searchbar config error:", data.error)
                    showDefaultSearchbar(wrapper)
                    return
                }

                var content = createSearchbarHTML(data)
                wrapper.innerHTML = content

                // Add form submission handler
                addFormSubmissionHandler()

                // Set selected values from URL parameters
                setSelectedValuesFromURL()
            })
            .catch(function (error) {
                console.error("Failed to load searchbar config:", error)
                showDefaultSearchbar(wrapper)
            })
    }

    function addFormSubmissionHandler() {
        var form = document.querySelector("#searchbar_wrapper form")
        if (form) {
            form.addEventListener("submit", function (e) {
                e.preventDefault()
                console.log("=== FORM SUBMISSION ===")

                var formData = new FormData(form)
                var params = new URLSearchParams()

                // Convert our field names to theme_prime format
                formData.forEach(function (value, key) {
                    if (value && value.trim() !== "") {
                        // Only add non-empty values
                        console.log("Processing field:", key, "=", value)
                        if (key === "category") {
                            // Category stays the same
                            params.append(key, value)
                            console.log("Added category:", value)
                        } else if (key.startsWith("attr_")) {
                            // Convert attr_X to attribute_value format: "X-value"
                            var attrId = key.replace("attr_", "")
                            var attributeValue = attrId + "-" + value
                            params.append("attribute_value", attributeValue)
                            console.log(
                                "Added attribute_value:",
                                attributeValue
                            )
                        } else if (key === "price_range") {
                            // Convert price_range to min_price and max_price
                            var parts = value.split("-")
                            if (parts.length === 2) {
                                params.append("min_price", parts[0])
                                params.append("max_price", parts[1])
                                console.log(
                                    "Added price range:",
                                    parts[0],
                                    "-",
                                    parts[1]
                                )
                            }
                        } else if (key === "tags") {
                            // Tags stay the same
                            params.append(key, value)
                            console.log("Added tags:", value)
                        }
                    }
                })

                console.log("Final params:", params.toString())

                // this new code added for loading show and hide 
                const loader = document.getElementById("loadingOverlay");
                console.log("---------------loader-------------------",loader)
                if (loader) loader.style.display = "block";


                var shopUrl = "/shop?" + params.toString()
                console.log("Redirecting to:", shopUrl)
                setTimeout(() => {
                    console.log("-------------inside settimeout ----------------------------------")
                window.location.href = shopUrl;
                }, 300);

                // this is comment code and add above code for showing loading 

                // Test the debug endpoint first
                // fetch("/alt/searchbar/debug?" + params.toString())
                //     .then(function (response) {
                //         return response.json()
                //     })
                //     .then(function (data) {
                //         console.log("Debug response:", data)

                //         // Redirect to shop with converted parameters
                //         var shopUrl = "/shop?" + params.toString()
                //         console.log("Redirecting to:", shopUrl)
                //         window.location.href = shopUrl
                //     })
                //     .catch(function (error) {
                //         console.error("Debug error:", error)

                //         // Still redirect even if debug fails
                //         var shopUrl = "/shop?" + params.toString()
                //         console.log("Redirecting to:", shopUrl)
                //         window.location.href = shopUrl
                //     })
            })
        }
    }

    function setSelectedValuesFromURL() {
        console.log("=== SETTING VALUES FROM URL ===")
        // Get URL parameters
        var urlParams = new URLSearchParams(window.location.search)
        console.log("URL params:", window.location.search)

        // Set category
        var category = urlParams.get("category")
        console.log("Category from URL:", category)
        if (category) {
            var categorySelect = document.querySelector(
                'select[name="category"]'
            )
            console.log("Category select found:", categorySelect)
            if (categorySelect) {
                try {
                    categorySelect.value = category
                    console.log("Set category value to:", category)
                } catch (e) {
                    console.warn("Error setting category value:", e)
                }
            } else {
                console.warn("Category select not found")
            }
        }

        // Set price range
        var minPrice = urlParams.get("min_price")
        var maxPrice = urlParams.get("max_price")
        console.log("Price range from URL:", minPrice, "-", maxPrice)
        if (minPrice || maxPrice) {
            var priceSelect = document.querySelector(
                'select[name="price_range"]'
            )
            console.log("Price select found:", priceSelect)
            if (priceSelect) {
                // Find the option that matches the price range
                var priceRange = minPrice + "-" + maxPrice
                var option = priceSelect.querySelector(
                    'option[value="' + priceRange + '"]'
                )
                if (option) {
                    try {
                        priceSelect.value = priceRange
                        console.log("Set price range value to:", priceRange)
                    } catch (e) {
                        console.warn("Error setting price range value:", e)
                    }
                }
            } else {
                console.warn("Price select not found")
            }
        }

        // Set attributes (theme_prime uses attribute_value)
        urlParams.forEach(function (value, key) {
            if (key === "attribute_value") {
                console.log("Attribute from URL:", key, "=", value)
                // Parse attribute_value format: "attribute_id-value_id"
                var parts = value.split("-")
                if (parts.length === 2) {
                    var attrId = parts[0]
                    var valueId = parts[1]
                    var attrSelect = document.querySelector(
                        'select[name="attr_' + attrId + '"]'
                    )
                    console.log("Attribute select found:", attrSelect)
                    if (attrSelect) {
                        try {
                            attrSelect.value = valueId
                            console.log(
                                "Set attribute",
                                attrId,
                                "value to:",
                                valueId
                            )
                        } catch (e) {
                            console.warn("Error setting attribute value:", e)
                        }
                    } else {
                        console.warn("Attribute select not found for:", attrId)
                    }
                }
            }
        })

        // Set tags
        var tags = urlParams.get("tags")
        console.log("Tags from URL:", tags)
        if (tags) {
            var tagsSelect = document.querySelector('select[name="tags"]')
            console.log("Tags select found:", tagsSelect)
            if (tagsSelect) {
                try {
                    tagsSelect.value = tags
                    console.log("Set tags value to:", tags)
                } catch (e) {
                    console.warn("Error setting tags value:", e)
                }
            } else {
                console.warn("Tags select not found")
            }
        }

        console.log("=== FINISHED SETTING VALUES ===")

        // If we have search parameters, show a message about filtering
        if (
            category ||
            minPrice ||
            maxPrice ||
            urlParams.has("attribute_value") ||
            tags
        ) {
            showFilterMessage()
        }
    }

    function showFilterMessage() {
        console.log("=== SHOWING FILTER MESSAGE ===")

        // Check if we're on the shop page
        if (window.location.pathname === "/shop") {
            var urlParams = new URLSearchParams(window.location.search)
            var filters = []

            var category = urlParams.get("category")
            if (category) {
                var categorySelect = document.querySelector(
                    'select[name="category"]'
                )
                if (categorySelect) {
                    var selectedOption = categorySelect.querySelector(
                        'option[value="' + category + '"]'
                    )
                    if (selectedOption) {
                        filters.push("קטגוריה: " + selectedOption.textContent)
                    }
                }
            }

            var minPrice = urlParams.get("min_price")
            var maxPrice = urlParams.get("max_price")
            if (minPrice || maxPrice) {
                var priceSelect = document.querySelector(
                    'select[name="price_range"]'
                )
                if (priceSelect) {
                    var priceRange = minPrice + "-" + maxPrice
                    var selectedOption = priceSelect.querySelector(
                        'option[value="' + priceRange + '"]'
                    )
                    if (selectedOption) {
                        filters.push("מחיר: " + selectedOption.textContent)
                    }
                }
            }

            var tags = urlParams.get("tags")
            if (tags) {
                var tagsSelect = document.querySelector('select[name="tags"]')
                if (tagsSelect) {
                    var selectedOption = tagsSelect.querySelector(
                        'option[value="' + tags + '"]'
                    )
                    if (selectedOption) {
                        filters.push("תגית: " + selectedOption.textContent)
                    }
                }
            }

            // Count attribute filters
            var attrCount = 0
            urlParams.forEach(function (value, key) {
                if (key === "attribute_value" && value) {
                    attrCount++
                }
            })

            if (attrCount > 0) {
                filters.push("פילטרים נוספים: " + attrCount)
            }

            // if (filters.length > 0) {
            //     // Create filter message
            //     var messageHtml = '<div class="alert alert-info mb-3">'
            //     messageHtml +=
            //         "<strong>סינון פעיל:</strong> " + filters.join(", ")
            //     messageHtml +=
            //         ' <a href="/shop" class="btn btn-sm btn-outline-secondary ms-2">נקה סינון</a>'
            //     messageHtml += "</div>"

            //     // Insert message at the top of the shop page
            //     var shopContainer = document.querySelector(".oe_website_sale")
            //     if (shopContainer) {
            //         shopContainer.insertAdjacentHTML("afterbegin", messageHtml)
            //     }
            // }
        }
    }

    function showDefaultSearchbar(wrapper) {
        console.log("Showing default searchbar")
        var defaultData = {
            categories: [],
            attributes: [],
            tags: [],
            show_price_filter: true,
            price_ranges: [
                { min: 800, max: 2000, label: "₪ 800 עד ₪ 2,000" },
                { min: 2000, max: 4000, label: "₪ 2,000 עד ₪ 4,000" },
                { min: 4000, max: 7000, label: "₪ 4,000 עד ₪ 7,000" },
                { min: 7000, max: 8000, label: "₪ 7,000 עד ₪ 8,000" },
            ],
        }
        var content = createSearchbarHTML(defaultData)
        wrapper.innerHTML = content

        // Add form submission handler
        addFormSubmissionHandler()

        // Set selected values from URL parameters
        setSelectedValuesFromURL()
    }

    function createSearchbarHTML(data) {
        console.log("=== CREATING SEARCHBAR HTML ===")
        console.log("Creating HTML with data:", data)
        var html = '<div class="container d-flex justify-content-center">'
        html += '<div id="loadingOverlay" class="loading" style="display:none;">Loading…</div>'
        html +=
            '<form class="row g-2 justify-content-center align-items-end" method="GET" action="/shop" style="max-width: 1200px; width: 100%;">'

        // Categories
        if (data.categories && data.categories.length > 0) {
            console.log("Adding categories:", data.categories)
            html += '<div class="col-sm-2 mb-2">'
            //html += '<label class="form-label">קטגוריה</label>'
            html += '<select class="form-select" name="category">'
            html += '<option value="">כל הקטגוריות</option>'
            data.categories.forEach(function (category) {
                console.log(
                    "Adding category option:",
                    category[0],
                    "=",
                    category[1]
                )
                html +=
                    '<option value="' +
                    category[0] +
                    '">' +
                    category[1] +
                    "</option>"
            })
            html += "</select>"
            html += "</div>"
        } else {
            console.log("No categories found in data")
        }

        // Attributes - using theme_prime format: attribute_value
        if (data.attributes && data.attributes.length > 0) {
            console.log("Adding attributes:", data.attributes)
            data.attributes.forEach(function (attr) {
                console.log("Adding attribute:", attr[0], "=", attr[1])
                html += '<div class="col-sm-2 mb-2">'
                //html += '<label class="form-label">' + attr[1] + "</label>"
                html +=
                    '<select class="form-select" name="attr_' + attr[0] + '">'
                html += '<option value="">' + attr[1] + "</option>"
                if (attr[2] && attr[2].length > 0) {
                    attr[2].forEach(function (value) {
                        console.log(
                            "Adding attribute value:",
                            value[0],
                            "=",
                            value[1]
                        )
                        html +=
                            '<option value="' +
                            value[0] +
                            '">' +
                            value[1] +
                            "</option>"
                    })
                }
                html += "</select>"
                html += "</div>"
            })
        } else {
            console.log("No attributes found in data")
        }

        // Tags
        if (data.tags && data.tags.length > 0) {
            console.log("Adding tags:", data.tags)
            html += '<div class="col-sm-2 mb-2">'
            //html += '<label class="form-label">תגיות</label>'
            html += '<select class="form-select" name="tags">'
            html += '<option value="">כל התגיות</option>'
            data.tags.forEach(function (tag) {
                console.log("Adding tag option:", tag[0], "=", tag[1])
                html += '<option value="' + tag[0] + '">' + tag[1] + "</option>"
            })
            html += "</select>"
            html += "</div>"
        } else {
            console.log("No tags found in data")
        }

        // Price filter - using theme_prime format: min_price and max_price
        if (data.show_price_filter && data.price_ranges) {
            console.log("Adding price filter with ranges:", data.price_ranges)
            html += '<div class="col-sm-2 mb-2">'
            //html += '<label class="form-label">טווח מחיר</label>'
            html += '<select class="form-select" name="price_range">'
            html += '<option value="">טווח המחירים</option>'
            data.price_ranges.forEach(function (range) {
                console.log(
                    "Adding price range option:",
                    range.min + "-" + range.max,
                    "=",
                    range.label
                )
                html +=
                    '<option value="' +
                    range.min +
                    "-" +
                    range.max +
                    '">' +
                    range.label +
                    "</option>"
            })
            html += "</select>"
            html += "</div>"
        } else {
            console.log("No price filter or ranges found in data")
        }
        // Submit button
        html +=
            '<div class="col-sm-2 mb-2 align-self-end"><button type="submit" class="btn btn-secondary w-100">התאימו לי אופניים</button></div>'
        html += '<div class="row justify-content-center d-sm-none">'
        //html +=
        //    '<button id="reset_button" type="button" class="btn btn-primary me-2">אִתחוּל</button>'
        html +=
            '<div class="col-sm-2 mt-2"><button id="close_button" type="button" class="btn btn-primary w-100" title="Close">סגירה</button></div>'
        html += "</div>"
        html += "</form>"
        html += "</div>"

        console.log("Generated HTML:", html)
        console.log("=== FINISHED CREATING HTML ===")
        return html
    }

    // Initialize when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSearchbar)
    } else {
        initSearchbar()
    }
})()
;(function () {
    "use strict"

    function loadSearchbar(wrapper) {
        fetch("/alt/searchbar/view")
            .then(response => response.json())
            .then(data => {
                const html = createSearchbarHTML(data)
                wrapper.innerHTML = html
            })
    }

    function createSearchbarHTML(data) {
        const html = data.template_html || ""
        return html
    }

    const wrapper = document.getElementById("searchbar_wrapper")
    const toggleButtons = document.querySelectorAll('[href="#search-wizard"]')

    if (wrapper && toggleButtons.length > 0) {
        toggleButtons.forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.preventDefault()

                if (!wrapper.classList.contains("d-none")) {
                    wrapper.classList.add("d-none")
                    return
                }

                if (wrapper.innerHTML.trim() === "") {
                    loadSearchbar(wrapper)
                }

                wrapper.classList.remove("d-none")
            })
        })
    }
})()
