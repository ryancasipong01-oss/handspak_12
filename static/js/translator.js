
document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");
    const suggestions = document.getElementById("suggestions");
    const gestureResult = document.getElementById("gestureResult");
    const letterResults = document.getElementById("letterResults");

    if (!searchInput || !suggestions || !gestureResult || !letterResults) {
        console.error("Translator elements are missing.");
        return;
    }

    let searchVersion = 0;

    // =====================================================
    // INPUT EVENT - AUTOMATIC TYPING
    // =====================================================

    searchInput.addEventListener("input", function () {

        const text = this.value.trim().toUpperCase();

        const currentVersion = ++searchVersion;

        suggestions.replaceChildren();
        gestureResult.replaceChildren();
        letterResults.replaceChildren();

        if (!text) {
            gestureResult.textContent =
                "Start typing to see a gesture.";
            return;
        }

        // Search complete letter, number, or word
        searchGesture(text, currentVersion);

        // Display individual letter gestures
        if (text.length > 1) {
            displayLetters(text, currentVersion);
        }

        // Show matching suggestions
        showSuggestions(text, currentVersion);

    });


    // =====================================================
    // SEARCH GESTURE
    // =====================================================

    async function searchGesture(text, version) {

        try {

            const response = await fetch(
                `/api/gesture/${encodeURIComponent(text)}`
            );

            if (!response.ok) {
                throw new Error("Gesture request failed.");
            }

            const data = await response.json();

            // Ignore outdated typing requests
            if (version !== searchVersion) return;

            if (data.success) {

                const card = document.createElement("div");
                card.className = "gesture-card";

                const heading = document.createElement("h2");
                heading.textContent = data.text || text;

                const image = document.createElement("img");
                image.src = data.image;
                image.alt = text + " sign language gesture";
                image.className = "gesture-image";

                image.onerror = function () {
                    this.alt = "Gesture image not found";
                };

                const category = document.createElement("span");
                category.className = "category";
                category.textContent = data.category || "Gesture";

                card.append(heading, image, category);

                gestureResult.replaceChildren(card);

            } else {

                gestureResult.textContent =
                    `No matching gesture found for "${text}".`;

            }

        } catch (error) {

            if (version === searchVersion) {
                console.error("Search error:", error);

                gestureResult.textContent =
                    "Unable to load gesture. Please try again.";
            }

        }

    }


    // =====================================================
    // DISPLAY INDIVIDUAL LETTER IMAGES
    // =====================================================

    async function displayLetters(text, version) {

        const characters = text.split("");

        const results = await Promise.all(
            characters.map(async function (character) {

                if (character === " ") {
                    return { character, space: true };
                }

                try {

                    const response = await fetch(
                        `/api/gesture/${encodeURIComponent(character)}`
                    );

                    if (!response.ok) return null;

                    const data = await response.json();

                    if (data.success) {
                        return {
                            character,
                            image: data.image
                        };
                    }

                } catch (error) {
                    console.error("Letter error:", error);
                }

                return null;

            })
        );

        // Do not display results from previous input
        if (version !== searchVersion) return;

        letterResults.replaceChildren();

        results.forEach(function (item) {

            if (!item) return;

            if (item.space) {

                const space = document.createElement("div");
                space.className = "space-character";

                letterResults.appendChild(space);
                return;

            }

            const card = document.createElement("div");
            card.className = "letter-card";

            const heading = document.createElement("h3");
            heading.textContent = item.character;

            const image = document.createElement("img");
            image.src = item.image;
            image.alt = item.character + " sign";
            image.loading = "lazy";

            image.onerror = function () {
                card.remove();
            };

            card.append(heading, image);

            letterResults.appendChild(card);

        });

    }


    // =====================================================
    // SUGGESTIONS
    // =====================================================

    async function showSuggestions(text, version) {

        try {

            const response = await fetch(
                `/api/suggestions?q=${encodeURIComponent(text)}`
            );

            if (!response.ok) return;

            const data = await response.json();

            if (version !== searchVersion) return;

            suggestions.replaceChildren();

            if (!Array.isArray(data)) return;

            data.forEach(function (item) {

                const button = document.createElement("button");

                button.type = "button";
                button.className = "suggestion-button";

                button.textContent =
                    `${item.name} (${item.category})`;

                button.addEventListener("click", function () {

                    searchInput.value = item.name;

                    const selectedVersion = ++searchVersion;

                    suggestions.replaceChildren();
                    gestureResult.replaceChildren();
                    letterResults.replaceChildren();

                    searchGesture(item.name, selectedVersion);

                    if (item.name.length > 1) {
                        displayLetters(item.name, selectedVersion);
                    }

                });

                suggestions.appendChild(button);

            });

        } catch (error) {

            console.error("Suggestion error:", error);

        }

    }


    // =====================================================
    // CLEAR TRANSLATOR
    // =====================================================

    window.clearTranslator = function () {

        searchVersion++;

        searchInput.value = "";

        suggestions.replaceChildren();
        letterResults.replaceChildren();

        gestureResult.textContent =
            "Start typing to see a gesture.";

        searchInput.focus();

    };

});
