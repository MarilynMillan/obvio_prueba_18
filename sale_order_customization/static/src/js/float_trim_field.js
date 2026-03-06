/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatField } from "@web/views/fields/float/float_field";

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export class FloatTrimField extends FloatField {
  get formattedValue() {
    const res = super.formattedValue;
    if (!res) return res;

    const dec = this.env.services.localization.decimalPoint || ".";
    const decEsc = escapeRegExp(dec);

    if (!res.includes(dec)) return res;

    // "1.00" -> "1", "2.50" -> "2.5"
    let out = res.replace(new RegExp(`(${decEsc}\\d*?)0+$`), "$1");
    out = out.replace(new RegExp(`${decEsc}$`), "");
    return out;
  }
}

registry.category("fields").add("float_trim", {
  component: FloatTrimField,
  supportedTypes: ["float"],
  extractProps: FloatField.extractProps,
});