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
 *
 * Allocation. Every label binding in the interface calls into this object, a
 * few hundred of them while a page is built, and most call it twice (text and
 * textFormat). The rules are therefore compiled once, and every result is
 * remembered by its input: a label is formatted the first time it is seen and
 * looked up after that. This is not an optimisation for its own sake. When
 * each call built its ~40 regular expressions afresh, the allocation it caused
 * during a page switch let Qt 6.10's incremental garbage collector run across
 * the switch and free objects still in use: the application crashed in Qt6Qml
 * (Nozzle Lab -> Thermochemistry, 8 of 9 runs). See
 * docs/engineering/implementation/NOTATION_NAVIGATION_CRASH.md.
 */
QtObject {
    id: notation

    // Boundaries without lookbehind, which the QML JavaScript engine does not
    // guarantee. ">" and "<" are excluded so a symbol already wrapped in a tag
    // is never wrapped twice.
    readonly property string boundaryBefore: "(^|[^A-Za-z0-9_>\.])"
    readonly property string boundaryAfter: "(?=$|[^A-Za-z0-9_<])"
    readonly property string letterClass: "[A-Za-zα-ω]"

    // Any authored markup -- not only notation. A label that already carries
    // <b> or <br> (the Equation Library does) is rich by intent and must pass
    // through untouched rather than be escaped into visible tags. No /g flag:
    // the expression is shared, and test() on a global one would keep state.
    readonly property var markup: /<\/?(i|b|u|sub|sup|br|p|font|span|a|small|big)\b[^>]*>/

    // The notation rules, compiled once, in the order they must run.
    readonly property var rules: notation.compileRules()

    // Results by input. Pure functions of their input, so a cached value can
    // never be stale. Bounded, because status text carries numbers that change.
    readonly property var memo: ({ rich: new Map(), species: new Map(),
                                   section: new Map(), runs: new Map() })
    readonly property int memoLimit: 4096

    function remember(map, key, value) {
        if (map.size >= notation.memoLimit)
            map.clear()
        map.set(key, value)
        return value
    }

    function escapeText(text) {
        return String(text).replace(/&/g, "&amp;")
                           .replace(/</g, "&lt;")
                           .replace(/>/g, "&gt;")
    }

    function hasMarkup(text) {
        return notation.markup.test(String(text))
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

    // [expression, replacement] pairs, applied in this order by format().
    function compileRules() {
        var B = notation.boundaryBefore
        var E = notation.boundaryAfter
        var L = notation.letterClass
        function g(source) { return new RegExp(source, "g") }
        return [
            // Area ratios and special starred quantities
            [g(B + "A/A\\*" + E), "$1<i>A</i>/<i>A</i>*"],
            [g(B + "T/T\\*" + E), "$1<i>T</i>/<i>T</i>*"],
            [g(B + "p/p\\*" + E), "$1<i>p</i>/<i>p</i>*"],
            [g(B + "ρ/ρ\\*" + E), "$1<i>ρ</i>/<i>ρ</i>*"],
            [g(B + "u/u\\*" + E), "$1<i>u</i>/<i>u</i>*"],
            [g(B + "p₀/p₀\\*" + E), "$1<i>p</i><sub>0</sub>/<i>p</i><sub>0</sub>*"],
            [g(B + "T₀/T₀\\*" + E), "$1<i>T</i><sub>0</sub>/<i>T</i><sub>0</sub>*"],
            [g(B + "p₀₂/p₁" + E), "$1<i>p</i><sub>02</sub>/<i>p</i><sub>1</sub>"],
            [g(B + "Δs/R" + E), "$1Δ<i>s</i>/<i>R</i>"],
            [g(B + "4f_F L\\*/D" + E), "$14 <i>f</i><sub>F</sub> <i>L</i>*/<i>D</i>"],
            [g(B + "A\\*/A" + E), "$1<i>A</i>*/<i>A</i>"],
            [g(B + "Ae/At" + E), "$1<i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>"],
            [g(B + "A_e/A_t" + E), "$1<i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>"],
            [g(B + "A_s/A_t" + E), "$1<i>A</i><sub>s</sub>/<i>A</i><sub>t</sub>"],
            [g(B + "A₂\\*/A₁\\*" + E), "$1<i>A</i><sub>2</sub>*/<i>A</i><sub>1</sub>*"],

            // Gas dynamics and shock pressure/density/temperature ratios
            [g(B + "p₀/p" + E), "$1<i>p</i><sub>0</sub>/<i>p</i>"],
            [g(B + "p/p₀" + E), "$1<i>p</i>/<i>p</i><sub>0</sub>"],
            [g(B + "ρ₀/ρ" + E), "$1<i>ρ</i><sub>0</sub>/<i>ρ</i>"],
            [g(B + "ρ/ρ₀" + E), "$1<i>ρ</i>/<i>ρ</i><sub>0</sub>"],
            [g(B + "T₀/T" + E), "$1<i>T</i><sub>0</sub>/<i>T</i>"],
            [g(B + "T/T₀" + E), "$1<i>T</i>/<i>T</i><sub>0</sub>"],
            [g(B + "p_b/p₀" + E), "$1<i>p</i><sub>b</sub>/<i>p</i><sub>0</sub>"],
            [g(B + "p_e/p₀" + E), "$1<i>p</i><sub>e</sub>/<i>p</i><sub>0</sub>"],
            [g(B + "p_e/p_b" + E), "$1<i>p</i><sub>e</sub>/<i>p</i><sub>b</sub>"],
            [g(B + "p₂/p₁" + E), "$1<i>p</i><sub>2</sub>/<i>p</i><sub>1</sub>"],
            [g(B + "p₀₂/p₀₁" + E), "$1<i>p</i><sub>02</sub>/<i>p</i><sub>01</sub>"],

            // Named forms first, so the generic rules never see their parts.
            [g(B + "gamma_([A-Za-z]+)" + E),
             function (m, pre, sub) { return pre + notation.subscripted("γ", sub) }],
            [g(B + "cp/cv" + E), "$1<i>c</i><sub><i>p</i></sub>/<i>c</i><sub><i>v</i></sub>"],
            [g(B + "Isp" + E), "$1<i>I</i><sub>sp</sub>"],
            [g(B + "Cf_([A-Za-z0-9]+)" + E), "$1<i>C</i><sub>f,$2</sub>"],
            [g(B + "Cf" + E), "$1<i>C</i><sub>f</sub>"],
            [g(B + "gamma" + E), "$1<i>γ</i>"],
            [g(B + "c\\*"), "$1<i>c</i>*"],
            [g(B + "mdot" + E), "$1<i>ṁ</i>"],
            [g(B + "ṁ" + E), "$1<i>ṁ</i>"],
            [g(B + "L(\\*?)/D" + E), "$1<i>L</i>$2/<i>D</i>"],

            // Mn₁: the normal component of a Mach number, M sub n,1.
            [g(B + "Mn([₀-₉]+)" + E),
             function (m, pre, digits) {
                 return pre + "<i>M</i><sub>n," + notation.subscriptDigits(digits) + "</sub>"
             }],
            // (RT₀), (Ap₀): a product of two symbols written without a space.
            [/\(([A-Za-z])([A-Za-z])([₀-₉]+)\)/g,
             function (m, a, b, digits) {
                 return "(<i>" + a + "</i><i>" + b + "</i><sub>"
                        + notation.subscriptDigits(digits) + "</sub>)"
             }],

            // x_sub: a single-letter symbol with a written subscript.
            [g(B + "(" + L + ")_([A-Za-z0-9]+(?:,[A-Za-z0-9]+)*)" + E),
             function (m, pre, base, sub) { return pre + notation.subscripted(base, sub) }],

            // x₀: a single-letter symbol with a Unicode subscript digit.
            [g(B + "(" + L + ")([₀-₉]+)"),
             function (m, pre, base, digits) {
                 return pre + notation.italicSymbol(base) + "<sub>"
                        + notation.subscriptDigits(digits) + "</sub>"
             }],

            // Δx: the difference operator stays upright, the quantity is italic.
            [g(B + "Δ([A-Za-z])" + E), "$1Δ<i>$2</i>"],

            // A lowercase Greek letter standing alone is a quantity symbol -- also
            // after a coefficient, as in (γ+1)²/(4γ).
            [g("(^|[^A-Za-z_>\\.])([α-ω])" + E), "$1<i>$2</i>"],

            // "Description  X": the codebase writes a label's symbol after a double
            // space. A lone letter there is the symbol. M̄ keeps its macron.
            [/(  )([A-Za-z]̄?)(?=$| \[|  )/g, "$1<i>$2</i>"],

            // Mach number alone or in input labels: "M", "Start M", "End M", "Jump to M", "M = 1".
            [/(^| )(M)($| )/g, "$1<i>$2</i>$3"],
            [g(B + "M(?= = )"), "$1<i>M</i>"],

            // Characteristic velocity c* with superscript
            [/(^| )c\*(?=$| )/g, "$1<i>c</i>*"]
        ]
    }

    // rich() without the memo: the rules applied to one input.
    function format(s) {
        if (notation.hasMarkup(s))
            return s
        var out = notation.escapeText(s)
        var rules = notation.rules
        for (var i = 0; i < rules.length; ++i)
            out = out.replace(rules[i][0], rules[i][1])
        if (!notation.hasMarkup(out))
            return s
        // RichText collapses a newline into a space; the plain text meant a line break.
        return out.replace(/\n/g, "<br>")
    }

    /*
     * A label in notation, as RichText markup. Returns the text unchanged when
     * it is already rich, and the plain text itself when nothing in it is
     * notation.
     */
    function rich(text) {
        if (text === undefined || text === null)
            return ""
        var key = String(text)
        var known = notation.memo.rich.get(key)
        return known !== undefined ? known
                                   : notation.remember(notation.memo.rich, key, notation.format(key))
    }

    /*
     * A CEA species or reactant name, for a species column only -- never for
     * general labels, where a digit after a letter is a hash ("8e5df1cc") or a
     * number ("3.44737e6"), not a stoichiometric count.
     *
     * Shown in chemical case: CEA writes "HCL", "AL2O3(L)", "NH4CLO4(I)" and,
     * in the same library, "MgCL2"; a chemist reads HCl, Al2O3(L), NH4ClO4(I),
     * MgCl2. Only the LABEL changes -- the name stays the identity everywhere
     * it is a key. The rewrite is conservative and matches
     * rocketforge/application/species_notation.py exactly (held together by
     * tests/application/test_species_notation.py):
     *   - only a capital pair in speciesRecased is lowered, and never one that
     *     also reads as two one-letter elements: CO stays carbon monoxide,
     *     NO nitric oxide, HO2 a radical -- never cobalt, nobelium, holmium;
     *   - the result must read as a formula of real element symbols, or the
     *     name is shown as written ("HTPB", "RP-1", "CHOS-Binder");
     *   - a phase qualifier ("(L)", "(cr)", "(I)", "(II)") and a ",name"
     *     suffix are never recased.
     * Then the counts in the formula -- after an element or a ")" group -- are
     * lowered to subscripts. A name that is not a formula is returned as is.
     */
    readonly property var speciesElements: notation.symbolSet(
        "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni "
        + "Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I "
        + "Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt "
        + "Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr "
        + "Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og")
    readonly property var speciesRecased: notation.symbolSet(
        "AL AR BA BE BR CA CL CR FE GA GE HE HG KR LI MG MN MO NA NE RB SE SR TI "
        + "XE ZN ZR")
    readonly property var speciesQualifier: /\((?:L|cr|gr|a|b|c|s|g|I|II|III|IV)\)$/
    readonly property var speciesCore: /^[A-Za-z0-9()]+$/
    readonly property var speciesCounted: /^(?:[A-Z][A-Za-z]?[0-9]*|\((?:[A-Z][A-Za-z]?[0-9]*)+\)[0-9]*)+$/
    readonly property var speciesCounts: /([A-Za-z)])([0-9]+)/g
    readonly property var speciesDigit: /[0-9]/

    function symbolSet(text) {
        var out = {}
        var list = text.split(" ")
        for (var i = 0; i < list.length; ++i)
            out[list[i]] = true
        return out
    }

    function isOneLetterElement(ch) {
        return ch.length === 1 && notation.speciesElements[ch] === true
    }

    function speciesRecase(core) {
        var out = ""
        var i = 0
        while (i < core.length) {
            var pair = core.substr(i, 2)
            if (pair.length === 2
                    && pair[0] >= "A" && pair[0] <= "Z" && pair[1] >= "A" && pair[1] <= "Z"
                    && notation.speciesRecased[pair] === true
                    && !(notation.isOneLetterElement(pair[0])
                         && notation.isOneLetterElement(pair[1]))) {
                out += pair[0] + pair[1].toLowerCase()
                i += 2
            } else {
                out += core[i]
                i += 1
            }
        }
        return out
    }

    function speciesReadsAsFormula(core) {
        var depth = 0
        var i = 0
        while (i < core.length) {
            var ch = core[i]
            if (ch === "(") {
                depth += 1
                i += 1
            } else if (ch === ")") {
                depth -= 1
                if (depth < 0)
                    return false
                i += 1
            } else if (ch >= "0" && ch <= "9") {
                i += 1
            } else if (ch >= "A" && ch <= "Z") {
                var two = core.substr(i, 2)
                if (two.length === 2 && two[1] >= "a" && two[1] <= "z"
                        && notation.speciesElements[two] === true)
                    i += 2
                else if (notation.speciesElements[ch] === true)
                    i += 1
                else
                    return false
            } else {
                return false
            }
        }
        return depth === 0
    }

    function species(name) {
        if (name === undefined || name === null)
            return ""
        var key = String(name)
        var known = notation.memo.species.get(key)
        if (known !== undefined)
            return known
        var result = key
        var text = key
        var prefix = text.charAt(0) === "*" ? "*" : ""
        text = text.substr(prefix.length)
        var suffix = ""
        var comma = text.indexOf(",")
        if (comma >= 0) {
            suffix = text.substr(comma)
            text = text.substr(0, comma)
        }
        var qualifier = notation.speciesQualifier.exec(text)
        if (qualifier !== null) {
            suffix = qualifier[0] + suffix
            text = text.substr(0, text.length - qualifier[0].length)
        }
        var charge = ""
        var last = text.charAt(text.length - 1)
        if (last === "+" || last === "-") {
            charge = last
            text = text.substr(0, text.length - 1)
        }
        if (text.length > 0 && notation.speciesCore.test(text)) {
            var core = notation.speciesRecase(text)
            if (core !== text && !notation.speciesReadsAsFormula(core))
                core = text
            if (notation.speciesDigit.test(core) && notation.speciesCounted.test(core)) {
                notation.speciesCounts.lastIndex = 0
                result = notation.escapeText(prefix)
                         + core.replace(notation.speciesCounts, "$1<sub>$2</sub>")
                         + notation.escapeText(charge) + notation.escapeText(suffix)
            } else if (core !== text) {
                result = prefix + core + charge + suffix
            }
        }
        return notation.remember(notation.memo.species, key, result)
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
        var key = String(text)
        var known = notation.memo.section.get(key)
        if (known !== undefined)
            return known
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
        return notation.remember(notation.memo.section, key, out.replace(/\n/g, "<br>"))
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
     * fillText calls. Each run: { text, italic, sub, sup }. The array is
     * shared through the memo: callers read it and never modify it.
     */
    function runs(text) {
        var key = String(text)
        var known = notation.memo.runs.get(key)
        if (known !== undefined)
            return known
        var html = notation.rich(text)
        if (!notation.hasMarkup(html))
            return notation.remember(notation.memo.runs, key,
                                     [{ text: key, italic: false, sub: false, sup: false }])
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
        return notation.remember(notation.memo.runs, key, out)
    }
}
