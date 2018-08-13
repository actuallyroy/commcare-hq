hqDefine('app_manager/js/summary/case_summary', function() {
    var assertProperties = hqImport("hqwebapp/js/assert_properties"),
        initialPageData = hqImport("hqwebapp/js/initial_page_data"),
        models = hqImport("app_manager/js/summary/models"),
        utils = hqImport("app_manager/js/summary/utils");

    var propertyModel = function(property) {
        var self = _.extend({}, property);

        _.each(self.forms, function(form) {
            _.each(form.load_questions, function(questionAndCondition) {
                questionAndCondition.question = utils.questionModel(questionAndCondition.question);
            });
            _.each(form.save_questions, function(questionAndCondition) {
                questionAndCondition.question = utils.questionModel(questionAndCondition.question);
            });
        });

        self.isVisible = ko.observable(true);
        return self;
    };

    var caseTypeModel = function(caseType) {
        var self = _.extend({}, caseType);

        self.properties = _.map(caseType.properties, function(property) {
            return propertyModel(property);
        });

        // Convert these from objects to lists so knockout can process more easily
        self.relationshipList = _.map(_.keys(self.relationships), function(relationship) {
            return {
                relationship: relationship,
                caseType: self.relationships[relationship],
            };
        });
        self.openedByList = _.map(_.keys(self.opened_by), function(formId) {
            return {
                formId: formId,
                conditions: self.opened_by[formId].conditions,
            };
        });
        self.closedByList = _.map(_.keys(self.closed_by), function(formId) {
            return {
                formId: formId,
                conditions: self.closed_by[formId].conditions,
            };
        });

        self.isSelected = ko.observable(true);
        self.hasVisibleProperties = ko.observable(true);
        self.isVisible = ko.computed(function() {
            return self.isSelected() && self.hasVisibleProperties();
        });

        return self;
    };

    var caseSummaryModel = function(options) {
        var self = models.contentModel(_.extend(options, {
            query_label: gettext("Filter properties"),
            onQuery: function(query) {
                _.each(self.caseTypes, function(caseType) {
                    var hasVisible = false;
                    _.each(caseType.properties, function(property) {
                        var isVisible = !query || property.name.indexOf(query) !== -1;
                        property.isVisible(isVisible);
                        hasVisible = hasVisible || isVisible;
                    });
                    caseType.hasVisibleProperties(hasVisible || !query && !caseType.properties.length);
                });
            },
            onSelectMenuItem: function(selectedId) {
                _.each(self.caseTypes, function(caseType) {
                    caseType.isSelected(!selectedId || selectedId === caseType.name);
                });
            },
        }));

        assertProperties.assertRequired(options, ['case_types']);
        self.caseTypes = _.map(options.case_types, function(caseType) {
            return caseTypeModel(caseType);
        });

        self.showConditions = ko.observable(true);
        self.toggleConditions = function() {
            self.showConditions(!self.showConditions());
        };

        self.showCalculations = ko.observable(true);
        self.toggleCalculations = function() {
            self.showCalculations(!self.showCalculations());
        };

        return self;
    };

    $(function() {
        var caseTypes = initialPageData.get("case_metadata").case_types;

        var caseSummaryMenu = models.menuModel({
            items: _.map(caseTypes, function(caseType) {
                return models.menuItemModel({
                    id: caseType.name,
                    name: caseType.name,
                    icon: "fcc fcc-fd-external-case appnav-primary-icon",
                    has_errors: caseType.has_errors,
                    subitems: [],
                });
            }),
            viewAllItems: gettext("View All Cases"),
        });

        var caseSummaryContent = caseSummaryModel({
            case_types: caseTypes,
            form_name_map: initialPageData.get("form_name_map"),
            lang: initialPageData.get("lang"),
            langs: initialPageData.get("app_langs"),
            read_only: initialPageData.get("read_only"),
        });

        models.initSummary(caseSummaryMenu, caseSummaryContent);
    });
});
