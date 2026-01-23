/** @odoo-module **/

import {registry} from "@web/core/registry";

import {useService} from "@web/core/utils/hooks";

const {Component} = owl;

export class ReviewLogTable extends Component {
    setup() {
        this.collapse = false;
        this.orm = useService("orm");
        this.reviews = [];
    }
    _getReviewData() {
        const records = this.env.model.root.data.review_log_ids.records;
        console.log(this.env.model.root)
        const reviews = [];
        for (var i = 0; i < records.length; i++) {
            reviews.push(records[i].data);
        }
        return reviews;
    }
    onToggleCollapse(ev) {
        var $panelHeading = $(ev.currentTarget).closest(".panel-heading");
        if (this.collapse) {
            $panelHeading.next("div#collapse1").hide();
        } else {
            $panelHeading.next("div#collapse1").show();
        }
        this.collapse = !this.collapse;
    }
}

ReviewLogTable.template = "base_tier_validation.review_log.Collapse";

export const reviewLogTableComponent = {
    component: ReviewLogTable,
};

registry.category("fields").add("form.tier_review_log", reviewLogTableComponent);
