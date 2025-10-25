/** @odoo-module **/
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { BackorderExtDialog } from '../js/Adialog';
import { BackorderDialog } from '../js/Backorder_Dialog';
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


patch(BarcodePickingModel.prototype, {
    setup() {
        super.setup?.();
        this.dialogService = useService("dialog");
    },

    async validate() {
        const pickId = this.record.id;
        let blind = false;

        try {
            blind = await rpc('/web/dataset/call_kw', {
                model: 'stock.picking.type',
                method: 'can_show_blind_receipt',
                args: [pickId],
                kwargs: {},
            });
        } catch (e) {
            console.error("Error checking blind receipt", e);
        }


        if (this.config.restrict_scan_dest_location === 'mandatory' &&
            !this.lastScanned.destLocation && this.selectedLine) {
            return this.notification(_t("Destination location must be scanned"), { type: "danger" });
        }

        if (this.config.lines_need_to_be_packed &&
            this.currentState.lines.some(line => this._lineNeedsToBePacked(line))) {
            return this.notification(_t("All products need to be packed"), { type: "danger" });
        }

        await this._setUser();

        if (this.config.create_backorder === 'ask') {
            const uncompletedLines = [];
            const alreadyChecked = [];
            let atLeastOneLinePartiallyProcessed = false;

            for (let line of this.currentState.lines) {
                line = this._getParentLine(line) || line;
                if (alreadyChecked.includes(line.virtual_id)) continue;
                alreadyChecked.push(line.virtual_id);

                let qtyDone = line.qty_done;
                if (qtyDone < line.reserved_uom_qty) {
                    qtyDone += this.currentState.lines.reduce((sum, otherLine) => {
                        return otherLine.product_id.id === line.product_id.id &&
                               otherLine.move_id === line.move_id &&
                               !otherLine.reserved_uom_qty
                            ? sum + otherLine.qty_done
                            : sum;
                    }, 0);

                    if (qtyDone < line.reserved_uom_qty) {
                        uncompletedLines.push(line);
                    }
                }

                atLeastOneLinePartiallyProcessed ||= qtyDone > 0;
            }

            if (this.showBackOrderDialog && !blind && atLeastOneLinePartiallyProcessed && uncompletedLines.length) {
                this.trigger("playSound");
                return this.dialogService.add(BackorderDialog, {
                    displayUoM: this.groups.group_uom,
                    uncompletedLines,
                    onApply:  async () => {
                    await this.save();
                    const context = this.validateContext;
                    context['barcode_trigger'] = true;
                    const action = await this.orm.call(
                        this.resModel,
                        this.validateMethod,
                        [this.recordIds],
                        { context }
                    );
                    const options = {
                        onClose: ev => this._closeValidate(ev)
                    };
                    if (action && (action.res_model || action.type === "ir.actions.client")) {
                        if (action.type === "ir.actions.client") {
                            action.params = Object.assign(action.params || {}, options);
                        }
                        this.trigger("playSound");
                        return this.action.doAction(action, options);
                    }
                    return options.onClose();
                },// 👈 avoid `super.validate()` to prevent dialog loops
                });
            }
            if (this.showBackOrderDialog && blind && atLeastOneLinePartiallyProcessed && uncompletedLines.length) {
            return this.dialogService.add(BackorderExtDialog, {
                displayUoM: this.groups.group_uom,
                uncompletedLines: this.currentState.lines.filter(l => l.qty_done < l.reserved_uom_qty),
                onApply: async () => {
                    await this.save();
                    const context = this.validateContext;
                    context['barcode_trigger'] = true;
                    const action = await this.orm.call(
                        this.resModel,
                        this.validateMethod,
                        [this.recordIds],
                        { context }
                    );
                    const options = {
                        onClose: ev => this._closeValidate(ev)
                    };
                    if (action && (action.res_model || action.type === "ir.actions.client")) {
                        if (action.type === "ir.actions.client") {
                            action.params = Object.assign(action.params || {}, options);
                        }
                        this.trigger("playSound");
                        return this.action.doAction(action, options);
                    }
                    return options.onClose();
                },
                close: () => console.log("BackorderExtDialog closed"),
            });
        }

        if (this.record.return_id) {
            this.validateContext = {
                ...this.validateContext,
                picking_ids_not_to_backorder: this.resId,
            };
        }

        if (this.shouldOpenSignatureModal) {
            this.openSignatureDialog(true);
            return;
        }


        }

        // Default flow if no dialog condition matched
        await this.save();
        const context = this.validateContext;
        context['barcode_trigger'] = true;
        const action = await this.orm.call(
            this.resModel,
            this.validateMethod,
            [this.recordIds],
            { context },
        );
        const options = {
            onClose: ev => this._closeValidate(ev)
        };
        if (action && (action.res_model || action.type === "ir.actions.client")) {
            if (action.type === "ir.actions.client") {
                action.params = Object.assign(action.params || {}, options);
            }
            this.trigger("playSound");
            return this.action.doAction(action, options);
        }
        return options.onClose();
    },
});