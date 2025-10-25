import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { unaccent } from "@web/core/utils/strings";

patch(PartnerList.prototype, {
    setup() {
        super.setup(...arguments);
    },
    getPartners() {
        // Ticket - HT01480
        let searchWord = unaccent((this.state.query || "").trim(), false).toLowerCase();
        searchWord = searchWord.replace(/-/g, ""); // Remove dashes from input query
        const partners = this.pos.models["res.partner"].getAll();

        // Normalize stored phone numbers for comparison
        partners.forEach(partner => {
            if (partner.phone) {
                partner.normalizedPhone = partner.phone.replace(/-/g, ""); // Remove dashes from stored phone
            }
            if (partner.mobile) {
                partner.normalizedMobile = partner.mobile.replace(/-/g, "");
            }
        });

        const exactMatches = partners.filter((partner) => partner.exactMatch(searchWord));
        if (exactMatches.length > 0) {
            return exactMatches;
        }

        const availablePartners = searchWord
            ? partners.filter((p) => {
                  const normalizedSearchString = unaccent(p.searchString, false).toLowerCase();
                  return (
                      normalizedSearchString.includes(searchWord) ||
                      (p.normalizedPhone && p.normalizedPhone.includes(searchWord)) ||
                      (p.normalizedMobile && p.normalizedMobile.includes(searchWord))
                  );
              })
            : partners
                  .slice(0, 1000)
                  .toSorted((a, b) =>
                      this.props.partner?.id === a.id
                          ? -1
                          : this.props.partner?.id === b.id
                          ? 1
                          : (a.name || "").localeCompare(b.name || "")
                  );
        return availablePartners;
    }
});
