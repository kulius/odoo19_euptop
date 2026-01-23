/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

export class ReviewLogTable extends Component {
    static template = "base_tier_validation.review_log.Collapse";

    setup() {
        this.state = useState({ collapse: false });
        this.orm = useService("orm");
        this.reviews = [];
    }

    _getReviewData() {
        const records = this.env.model.root.data.review_log_ids.records;
        const reviews = [];
        for (let i = 0; i < records.length; i++) {
            reviews.push(records[i].data);
        }
        return reviews;
    }

    onToggleCollapse(ev) {
        const panelHeading = ev.currentTarget.closest(".panel-heading");
        const collapseDiv = panelHeading.nextElementSibling;
        if (collapseDiv && collapseDiv.id === "collapse1") {
            if (this.state.collapse) {
                collapseDiv.style.display = "none";
            } else {
                collapseDiv.style.display = "block";
            }
        }
        this.state.collapse = !this.state.collapse;
    }
}

export const reviewLogTableComponent = {
    component: ReviewLogTable,
};

registry.category("fields").add("form.tier_review_log", reviewLogTableComponent);
