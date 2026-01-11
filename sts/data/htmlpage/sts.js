(function (global, factory) {
  if (typeof exports === "object" && typeof module === "object") {
    // CommonJS
    Object.assign(exports, factory());
  } else if (typeof define === "function" && define.amd) {
    // AMD
    define(factory);
  } else {
    // Browser globals
    global = typeof globalThis !== "undefined" ? globalThis : global || self;
    global.sts = factory();
  }
}(this, function () {

  'use strict';

  class Unicode {
    static compositeLength(text, pos) {
      let i = pos;
      let total = text.length;
      let length = 1;
      let isIds = false;
      while (length && (i < total)) {
        let code = text.codePointAt(i);

        // check if the current char is a prefix composer
        if (code === 0x303E) {
          // ideographic variation indicator
          isIds = true;
          length += 1;
        } else if ((0x2FF0 <= code && code <= 0x2FF1) || (0x2FF4 <= code && code <= 0x2FFB)) {
          // IDS binary operator
          isIds = true;
          length += 2;
        } else if (0x2FF2 <= code && code <= 0x2FF3) {
          // IDS trinary operator
          isIds = true;
          length += 3;
        } else if (isIds && !(
          (0x4E00 <= code && code <= 0x9FFF)  // CJK unified
          || (0x3400 <= code && code <= 0x4DBF) || (0x20000 <= code && code <= 0x3FFFF)  // Ext-A, ExtB+
          || (0xF900 <= code && code <= 0xFAFF) || (0x2F800 <= code && code <= 0x2FA1F)  // Compatibility
          || (0x2E80 <= code && code <= 0x2FDF)  // Radical
          || (0x31C0 <= code && code <= 0x31EF)  // Stroke
          || (0xE000 <= code && code <= 0xF8FF) || (0xF0000 <= code && code <= 0x1FFFFF)  // Private
          || (code == 0xFF1F)  // ？
          || (0xFE00 <= code && code <= 0xFE0F) || (0xE0100 <= code && code <= 0xE01EF)  // VS
        )) {
          // check for a valid IDS to avoid a breaking on e.g.:
          //
          //     IDS包括⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，可用於…
          //
          // - IDS := Ideographic | Radical | CJK_Stroke | Private Use
          //        | U+FF1F | IDS_BinaryOperator IDS IDS
          //        | IDS_TrinaryOperator IDS IDS IDS
          //
          // - We also allow IVI and VS in an IDS.
          break;
        }

        i += (code > 0xFFFF) ? 2 : 1;

        // check if the next char is a postfix composer
        if (i < total) {
          code = text.codePointAt(i);
          if (0xFE00 <= code && code <= 0xFE0F) {
            // variation selectors
            length += 1;
          } else if (0xE0100 <= code && code <= 0xE01EF) {
            // variation selectors supplement
            length += 1;
          } else if (0x180B <= code && code <= 0x180D) {
            // Mongolian free variation selectors
            length += 1;
          } else if (0x0300 <= code && code <= 0x036F) {
            // combining diacritical marks
            length += 1;
          } else if (0x1AB0 <= code && code <= 0x1AFF) {
            // combining diacritical marks extended
            length += 1;
          } else if (0x1DC0 <= code && code <= 0x1DFF) {
            // combining diacritical marks supplement
            length += 1;
          } else if (0x20D0 <= code && code <= 0x20FF) {
            // combining diacritical marks for symbols
            length += 1;
          } else if (0xFE20 <= code && code <= 0xFE2F) {
            // combining half marks
            length += 1;
          }
        }

        length--;
      }
      return i - pos;
    }

    static split(text) {
      const rv = [];
      let i = 0;
      let total = text.length;
      while (i < total) {
        const len = Unicode.compositeLength(text, i);
        rv.push(text.slice(i, i + len));
        i += len;
      }
      return rv;
    }
  }

  function* chain(...args) {
    for (const arg of args) {
      yield* arg;
    }
  }

  const excludeReturnGroupPattern = /^return\d*$/;

  class StsDict {
    constructor(dict) {
      this.dict = dict;
    }

    static async load(url) {
      const response = await fetch(url);
      const dict = await response.json();
      return new StsDict(dict);
    }

    get(key) {
      let trie = this.dict;
      for (const chr of key) {
        trie = trie[chr];
        if (typeof trie === 'undefined') {
          return null;
        }
      }
      return trie[''] || null;
    }

    *entries() {
      const stack = [['', this.dict]];
      const substack = [];
      while (stack.length) {
        let [key, trie] = stack.pop();
        for (let chr in trie) {
          if (chr === '') {
            yield [key, trie[chr]];
          } else {
            substack.push([key + chr, trie[chr]]);
          }
        }
        while (substack.length) {
          stack.push(substack.pop());
        }
      }
    }

    add(key, values, important) {
      if (!Array.isArray(values)) {
        values = [values];
      }

      let current = this.dict;
      for (const chr of key) {
        if (typeof current[chr] === 'undefined') {
          current[chr] = {};
        }
        current = current[chr];
      }

      if (typeof current[''] === 'undefined') {
        current[''] = [];
      }
      const list = current[''];
      if (important) {
        const set = new Set(chain(values, list));
        list.length = 0;
        list.push(...set);
      } else {
        for (const value of values) {
          if (!list.includes(value)) {
            list.push(value);
          }
        }
      }
    }

    delete(key) {
      let trie = this.dict;
      for (const chr of key) {
        trie = trie[chr];
        if (typeof trie === 'undefined') {
          return;
        }
      }
      delete trie[''];
    }

    normalize(input) {
      if (typeof input === 'string') {
        return Unicode.split(input);
      }
      return input;
    }

    match(input, pos, maxpos=Infinity) {
      input = this.normalize(input)
      let trie = this.dict;
      let i = pos;
      let end = Math.min(input.length, maxpos);
      let match = null;
      let matchEnd = null;
      outer: while (i < end) {
        for (const chr of input[i]) {
          trie = trie[chr];
          if (!trie) {
            break outer;
          }
        }
        const values = trie[''];
        if (values) {
          match = values;
          matchEnd = i + 1;
        }
        i++;
      }
      if (match && match.length) {
        return {
          conv: {
            key: input.slice(pos, matchEnd),
            values: match,
          },
          start: pos,
          end: matchEnd,
        };
      }
      return null;
    }

    *apply(input) {
      input = this.normalize(input);
      let i = 0;
      let total = input.length;
      while (i < total) {
        let match = this.match(input, i);
        if (match) {
          yield match.conv;
          i = match.end;
        } else {
          yield input[i];
          i++;
        }
      }
    }

    *convert(text, exclude) {
      if (!exclude) {
        yield* this.apply(text);
        return;
      }

      yield* this.convertWithFilter(text, exclude);
    }

    *convertWithFilter(text, exclude) {
      let index = 0;
      let m;
      let t;
      exclude.lastIndex = 0;
      while (m = exclude.exec(text)) {
        const start = m.index;
        const end = exclude.lastIndex;

        t = text.slice(index, start);
        if (t) { yield* this.apply(t); }

        t = m[0];
        for (const key in m.groups) {
          if (!excludeReturnGroupPattern.test(key)) { continue; }
          const value = m.groups[key];
          if (typeof value === 'undefined') { continue; }
          t = value;
        }
        if (t)  { yield {text: t}; }

        index = end;
      }

      t = text.slice(index);
      if (t) { yield* this.apply(t); }
    }
  }

  return {
    Unicode,
    StsDict,
  };

}));
