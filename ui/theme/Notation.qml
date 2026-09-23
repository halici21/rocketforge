pragma Singleton
import QtQuick

/*
 * Mathematical notation for labels: one rule set, in one place.
 *
 * The backend keeps plain labels ("Chamber pressure  p_c"): they are test
 * contracts, and they are what reaches the clipboard and exported files, which
 * must never carry markup. The notation is applied here, at presentation, and
 * nowhere else.
 *
 * Rules (ISO 80000-2):
 *   - a quantity symbol is italic:            p, T, M, A, c, γ, θ, ρ
 *   - a descriptive subscript is upright:     p_c -> p<sub>c</sub> (c = chamber)
 *   - a subscript that is itself a quantity
 *     stays italic:                           c_p -> c<sub><i>p</i></sub>
 *   - operators and abbreviations stay upright: Δ, O/F, "sp" in Isp
 *
 * Why RichText, not StyledText: Qt Quick's StyledText silently drops <sub> and
 * <sup>, and AutoText resolves to StyledText, so a subscript written for either
 * is drawn on the baseline ("Isp" reads as "/sp"). Measured. Only RichText
 * draws them. RichText does not elide, so a component shows RichText only when
 * a label actually carries notation, and plain labels keep their eliding.
 *
 * Plain text is escaped before any rule runs: in RichText a literal "<" starts
 * a tag, and "p < p_crit" rendered as "p" and nothing after it. Measured.
 *
 * Text that is already rich -- it contains <i>, <sub> or <sup> -- was authored
 * deliberately and is passed through untouched.
 */
QtObject {
    id: notation

    // Boundaries without lookbehind, which the QML JavaScript engine does not
    // guarantee. ">" and "<" are excluded so a symbol already wrapped in a tag
    // is never wrapped twice.
    readonly property string boundaryBefore: "(^|[^A-Za-z0-9_>\.])"
    readonly property string boundaryAfter: "(?=$|[^A-Za-z0-9_<])"
    readonly property string letterClass: "[A-Za-zα-ω]"

    function escapeText(text) {
        return String(text).replace(/&/g, "&amp;")
                           .replace(/</g, "&lt;")
                           .replace(/>/g, "&gt;")
    }

    // Any authored markup -- not only notation. A label that already carries
    // <b> or <br> (the Equation Library does) is rich by intent and must pass
    // through untouched rather than be escaped into visible tags.
    function hasMarkup(text) {
        return /<\/?(i|b|u|sub|sup|br|p|font|span|a|small|big)\b[^>]*>/.test(String(text))
    }

    function italicSymbol(symbol) {
        return "<i>" + symbol + "</i>"
    }

    function subscripted(base, subscript) {
        var parts = subscript.split(",")
        for (var i = 0; i < parts.length; ++i) {
            // c_p and c_v: the p and v are quantities (constant pressure,
            // constant volume), not descriptions, so they stay italic.
            if (i === 0 && base === "c" && (parts[i] === "p" || parts[i] === "v"))
                parts[i] = notation.italicSymbol(parts[i])
        }
        return notation.italicSymbol(base) + "<sub>" + parts.join(",") + "</sub>"
    }

    function subscriptDigits(digits) {
        var map = { "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
                    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9" }
        var out = ""
        for (var i = 0; i < digits.length; ++i)
            out += map[digits[i]] !== undefined ? map[digits[i]] : digits[i]
        return out
    }

    /*
     * A label in notation, as RichText markup. Returns the text unchanged when
     * it is already rich, and escaped plain text when nothing in it is notation.
     */
    function rich(text) {
        if (text === undefined || text === null)
            return ""
        var s = String(text)
        if (notation.hasMarkup(s))
            return s
        s = notation.escapeText(s)
        var B = notation.boundaryBefore
        var E = notation.boundaryAfter

        // Area ratios and special starred quantities
        s = s.replace(new RegExp(B + "A/A\\*" + E, "g"), "$1" + "<i>A</i>/<i>A</i>*")
        s = s.replace(new RegExp(B + "T/T\\*" + E, "g"), "$1" + "<i>T</i>/<i>T</i>*")
        s = s.replace(new RegExp(B + "p/p\\*" + E, "g"), "$1" + "<i>p</i>/<i>p</i>*")
        s = s.replace(new RegExp(B + "ρ/ρ\\*" + E, "g"), "$1" + "<i>ρ</i>/<i>ρ</i>*")
        s = s.replace(new RegExp(B + "u/u\\*" + E, "g"), "$1" + "<i>u</i>/<i>u</i>*")
        s = s.replace(new RegExp(B + "p₀/p₀\\*" + E, "g"), "$1" + "<i>p</i><sub>0</sub>/<i>p</i><sub>0</sub>*")
        s = s.replace(new RegExp(B + "T₀/T₀\\*" + E, "g"), "$1" + "<i>T</i><sub>0</sub>/<i>T</i><sub>0</sub>*")
        s = s.replace(new RegExp(B + "p₀₂/p₁" + E, "g"), "$1" + "<i>p</i><sub>02</sub>/<i>p</i><sub>1</sub>")
        s = s.replace(new RegExp(B + "Δs/R" + E, "g"), "$1" + "Δ<i>s</i>/<i>R</i>")
        s = s.replace(new RegExp(B + "4f_F L\\*/D" + E, "g"), "$1" + "4 <i>f</i><sub>F</sub> <i>L</i>*/<i>D</i>")
        s = s.replace(new RegExp(B + "A\\*/A" + E, "g"), "$1" + "<i>A</i>*/<i>A</i>")
        s = s.replace(new RegExp(B + "Ae/At" + E, "g"), "$1" + "<i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>")
        s = s.replace(new RegExp(B + "A_e/A_t" + E, "g"), "$1" + "<i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>")
        s = s.replace(new RegExp(B + "A_s/A_t" + E, "g"), "$1" + "<i>A</i><sub>s</sub>/<i>A</i><sub>t</sub>")
        s = s.replace(new RegExp(B + "A₂\\*/A₁\\*" + E, "g"), "$1" + "<i>A</i><sub>2</sub>*/<i>A</i><sub>1</sub>*")

        // Gas dynamics and shock pressure/density/temperature ratios
        s = s.replace(new RegExp(B + "p₀/p" + E, "g"), "$1" + "<i>p</i><sub>0</sub>/<i>p</i>")
        s = s.replace(new RegExp(B + "p/p₀" + E, "g"), "$1" + "<i>p</i>/<i>p</i><sub>0</sub>")
        s = s.replace(new RegExp(B + "ρ₀/ρ" + E, "g"), "$1" + "<i>ρ</i><sub>0</sub>/<i>ρ</i>")
        s = s.replace(new RegExp(B + "ρ/ρ₀" + E, "g"), "$1" + "<i>ρ</i>/<i>ρ</i><sub>0</sub>")
        s = s.replace(new RegExp(B + "T₀/T" + E, "g"), "$1" + "<i>T</i><sub>0</sub>/<i>T</i>")
        s = s.replace(new RegExp(B + "T/T₀" + E, "g"), "$1" + "<i>T</i>/<i>T</i><sub>0</sub>")
        s = s.replace(new RegExp(B + "p_b/p₀" + E, "g"), "$1" + "<i>p</i><sub>b</sub>/<i>p</i><sub>0</sub>")
        s = s.replace(new RegExp(B + "p_e/p₀" + E, "g"), "$1" + "<i>p</i><sub>e</sub>/<i>p</i><sub>0</sub>")
        s = s.replace(new RegExp(B + "p_e/p_b" + E, "g"), "$1" + "<i>p</i><sub>e</sub>/<i>p</i><sub>b</sub>")
        s = s.replace(new RegExp(B + "p₂/p₁" + E, "g"), "$1" + "<i>p</i><sub>2</sub>/<i>p</i><sub>1</sub>")
        s = s.replace(new RegExp(B + "p₀₂/p₀₁" + E, "g"), "$1" + "<i>p</i><sub>02</sub>/<i>p</i><sub>01</sub>")

        // Named forms first, so the generic rules never see their parts.
        s = s.replace(new RegExp(B + "gamma_([A-Za-z]+)" + E, "g"),
                      function (m, pre, sub) { return pre + notation.subscripted("γ", sub) })
        s = s.replace(new RegExp(B + "cp/cv" + E, "g"),
                      "$1" + "<i>c</i><sub><i>p</i></sub>/<i>c</i><sub><i>v</i></sub>")
        s = s.replace(new RegExp(B + "Isp" + E, "g"), "$1" + "<i>I</i><sub>sp</sub>")
        s = s.replace(new RegExp(B + "Cf_([A-Za-z0-9]+)" + E, "g"), "$1" + "<i>C</i><sub>f,$2</sub>")
        s = s.replace(new RegExp(B + "Cf" + E, "g"), "$1" + "<i>C</i><sub>f</sub>")
        s = s.replace(new RegExp(B + "gamma" + E, "g"), "$1" + "<i>γ</i>")
        s = s.replace(new RegExp(B + "c\\*", "g"), "$1" + "<i>c</i>*")
        s = s.replace(new RegExp(B + "mdot" + E, "g"), "$1" + "<i>ṁ</i>")
        s = s.replace(new RegExp(B + "ṁ" + E, "g"), "$1" + "<i>ṁ</i>")
        s = s.replace(new RegExp(B + "L(\\*?)/D" + E, "g"), "$1" + "<i>L</i>$2/<i>D</i>")

        // Mn₁: the normal component of a Mach number, M sub n,1.
        s = s.replace(new RegExp(B + "Mn([₀-₉]+)" + E, "g"),
                      function (m, pre, digits) {
                          return pre + "<i>M</i><sub>n," + notation.subscriptDigits(digits) + "</sub>"
                      })
        // (RT₀), (Ap₀): a product of two symbols written without a space.
        s = s.replace(/\(([A-Za-z])([A-Za-z])([₀-₉]+)\)/g,
                      function (m, a, b, digits) {
                          return "(<i>" + a + "</i><i>" + b + "</i><sub>"
                                 + notation.subscriptDigits(digits) + "</sub>)"
                      })

        // x_sub: a single-letter symbol with a written subscript.
        s = s.replace(new RegExp(B + "(" + notation.letterClass + ")_([A-Za-z0-9]+(?:,[A-Za-z0-9]+)*)" + E, "g"),
                      function (m, pre, base, sub) { return pre + notation.subscripted(base, sub) })

        // x₀: a single-letter symbol with a Unicode subscript digit.
        s = s.replace(new RegExp(B + "(" + notation.letterClass + ")([₀-₉]+)", "g"),
                      function (m, pre, base, digits) {
                          return pre + notation.italicSymbol(base) + "<sub>"
                                 + notation.subscriptDigits(digits) + "</sub>"
                      })

        // Δx: the difference operator stays upright, the quantity is italic.
        s = s.replace(new RegExp(B + "Δ([A-Za-z])" + E, "g"), "$1" + "Δ<i>$2</i>")

        // A lowercase Greek letter standing alone is a quantity symbol -- also
        // after a coefficient, as in (γ+1)²/(4γ).
        s = s.replace(new RegExp("(^|[^A-Za-z_>\\.])([α-ω])" + E, "g"), "$1" + "<i>$2</i>")

        // "Description  X": the codebase writes a label's symbol after a double
        // space. A lone letter there is the symbol. M̄ keeps its macron.
        s = s.replace(/(  )([A-Za-z]̄?)(?=$| \[|  )/g, "$1<i>$2</i>")

        // Mach number alone or in input labels: "M", "Start M", "End M", "Jump to M", "M = 1".
        s = s.replace(/(^| )(M)($| )/g, "$1<i>$2</i>$3")
        s = s.replace(new RegExp(B + "M(?= = )", "g"), "$1" + "<i>M</i>")

        // Characteristic velocity c* with superscript
        s = s.replace(/(^| )c\*(?=$| )/g, "$1<i>c</i>*")

        if (!notation.hasMarkup(s)) {
            return String(text)
        }
        // RichText collapses a newline into a space; the plain text meant a line break.
        return s.replace(/\n/g, "<br>")
    }

    /*
     * A CEA species or reactant name, for a species column only -- never for
     * general labels, where a digit after a letter is a hash ("8e5df1cc") or a
     * number ("3.44737e6"), not a stoichiometric count.
     *
     * The name is shown exactly as CEA writes it: its case ("AL2O3", not
     * "Al2O3") and its phase suffix ("(L)", "(cr)", "(I)", "(II)") are part of
     * the species identity and are never rewritten. Only the counts in the
     * formula part -- before a "(" suffix or a ",name" qualifier -- are lowered
     * to subscripts. A name that is not a formula ("HTPB R45M", "RP-1") is
     * returned unchanged.
     */
    function species(name) {
        if (name === undefined || name === null)
            return ""
        var s = String(name)
        var m = /^(\*?)([A-Za-z0-9]+)([+-]?)((?:\(|,).*)?$/.exec(s)
        if (m === null || !/^(?:[A-Z][A-Za-z]?[0-9]*)+$/.test(m[2]) || !/[0-9]/.test(m[2]))
            return s
        var formula = m[2].replace(/([A-Za-z])([0-9]+)/g, "$1<sub>$2</sub>")
        return notation.escapeText(m[1]) + formula + notation.escapeText(m[3])
               + notation.escapeText(m[4] === undefined ? "" : m[4])
    }

    function speciesFormat(name) {
        return notation.hasMarkup(notation.species(name)) ? Text.RichText : Text.PlainText
    }

    /*
     * rich(text) for an uppercase section label. Font.AllUppercase would turn
     * the quantity p into P and θ into Θ -- different symbols -- so the label
     * is uppercased here instead, prose only: italic symbols, subscripts and
     * Greek letters keep their case. Pair with a MixedCase font. Plain text
     * without notation comes back unchanged for the component to uppercase.
     */
    function sectionRich(text) {
        if (!notation.isRich(text))
            return text === undefined || text === null ? "" : String(text)
        var parts = notation.runs(text)
        var out = ""
        for (var i = 0; i < parts.length; ++i) {
            var run = parts[i]
            var symbol = run.italic || run.sub || run.sup
            var t = notation.escapeText(symbol ? run.text
                                               : run.text.replace(/[a-z]/g, function (c) {
                                                     return c.toUpperCase() }))
            if (run.italic) t = "<i>" + t + "</i>"
            if (run.sub) t = "<sub>" + t + "</sub>"
            if (run.sup) t = "<sup>" + t + "</sup>"
            out += t
        }
        return out.replace(/\n/g, "<br>")
    }

    function isRich(text) {
        return notation.hasMarkup(notation.rich(text))
    }

    // The textFormat to pair with rich(text): RichText only when needed, so a
    // plain label keeps Text's eliding, which RichText does not provide.
    function textFormat(text) {
        return notation.isRich(text) ? Text.RichText : Text.PlainText
    }

    // What rich(text) shows, as plain text: for tooltips, accessibility names
    // and anything else that cannot render markup.
    function plain(text) {
        var runs = notation.runs(text)
        var out = ""
        for (var i = 0; i < runs.length; ++i)
            out += runs[i].text
        return out
    }

    /*
     * rich(text) as runs a Canvas can draw one at a time -- a Canvas cannot
     * render markup, but it can switch to an italic or a smaller font between
     * fillText calls. Each run: { text, italic, sub, sup }.
     */
    function runs(text) {
        var html = notation.rich(text)
        if (!notation.hasMarkup(html)) {
            return [{ text: String(text), italic: false, sub: false, sup: false }]
        }
        var out = []
        var italic = 0, sub = 0, sup = 0
        var re = /<(\/?)(i|sub|sup)>|([^<]+|<)/g
        var match
        while ((match = re.exec(html)) !== null) {
            if (match[2] !== undefined) {
                var step = match[1] === "/" ? -1 : 1
                if (match[2] === "i") italic += step
                else if (match[2] === "sub") sub += step
                else sup += step
            } else {
                var raw = match[3] !== undefined ? match[3] : match[0]
                var chunk = raw.replace(/&lt;/g, "<").replace(/&gt;/g, ">")
                               .replace(/&amp;/g, "&")
                out.push({ text: chunk, italic: italic > 0, sub: sub > 0, sup: sup > 0 })
            }
        }
        return out
    }
}
