hqDefine('app_manager/js/summary/form_summary', function() {
    var assertProperties = hqImport("hqwebapp/js/assert_properties"),
        initialPageData = hqImport("hqwebapp/js/initial_page_data"),
        models = hqImport("app_manager/js/summary/models"),
        utils = hqImport('app_manager/js/summary/utils');

    var formSummaryModel = function(options) {
        var self = models.contentModel(_.extend(options, {
            query_label: gettext("Filter questions"),
            onQuery: function(query) {
                var match = function(needle, haystack) {
                    return !needle || haystack.toLowerCase().indexOf(needle.toLowerCase()) !== -1;
                };
                _.each(self.modules, function(module) {
                    var moduleIsVisible = match(query, self.translate(module.name));
                    _.each(module.forms, function(form) {
                        var formIsVisible = match(query, self.translate(form.name));
                        _.each(form.questions, function(question) {
                            var questionIsVisible = match(query, question.value + self.translateQuestion(question));
                            questionIsVisible = questionIsVisible || _.find(question.options, function(option) {
                                return match(query, option.value + self.translateQuestion(option));
                            });
                            question.isVisible(questionIsVisible);
                            formIsVisible = formIsVisible || questionIsVisible;
                        });
                        form.hasVisibleDescendants(formIsVisible);
                        moduleIsVisible = moduleIsVisible || formIsVisible;
                    });
                    module.hasVisibleDescendants(moduleIsVisible);
                });
            },
            onSelectMenuItem: function(selectedId) {
                _.each(self.modules, function(module) {
                    module.isSelected(!selectedId || selectedId === module.id || _.find(module.forms, function(f) { return selectedId === f.id }));
                    _.each(module.forms, function(form) {
                        form.isSelected(!selectedId || selectedId === form.id || selectedId === module.id);
                    });
                });
            },
        }));

        assertProperties.assertRequired(options, ['errors', 'modules']);
        self.errors = options.errors;
        self.modules = _.map(options.modules, moduleModel);

        self.showCalculations = ko.observable(false);
        self.toggleCalculations = function() {
            self.showCalculations(!self.showCalculations());
        };

        self.showRelevance = ko.observable(false);
        self.toggleRelevance = function() {
            self.showRelevance(!self.showRelevance());
        };

        self.showConstraints = ko.observable(false);
        self.toggleConstraints = function() {
            self.showConstraints(!self.showConstraints());
        };

        self.showComments = ko.observable(false);
        self.toggleComments = function() {
            self.showComments(!self.showComments());
        };

        self.showDefaultValues = ko.observable(false);
        self.toggleDefaultValues = function() {
            self.showDefaultValues(!self.showDefaultValues());
        };

        return self;
    };

    var moduleModel = function(module) {
        var self = _.extend({}, module);

        self.url = hqImport("hqwebapp/js/initial_page_data").reverse("view_module", self.id);
        self.icon = utils.moduleIcon(self) + ' hq-icon';
        self.forms = _.map(self.forms, formModel);

        self.isSelected = ko.observable(true);

        self.hasVisibleDescendants = ko.observable(true);
        self.isVisible = ko.computed(function() {
            return self.isSelected() && self.hasVisibleDescendants();
        });

        return self;
    };

    var formModel = function(form) {
        var self = _.extend({}, form);

        self.url = hqImport("hqwebapp/js/initial_page_data").reverse("form_source", self.id);
        self.icon = utils.formIcon(self) + ' hq-icon';
        self.questions = _.map(self.questions, function(question) {
            return utils.questionModel(question);
        });

        self.isSelected = ko.observable(true);

        self.hasVisibleDescendants = ko.observable(true);
        self.isVisible = ko.computed(function() {
            return self.isSelected() && self.hasVisibleDescendants();
        });

        return self;
    };

    $(function() {
        var lang = initialPageData.get('lang'),
            langs = initialPageData.get('langs');

        var formSummaryMenu = models.menuModel({
            items: _.map(initialPageData.get("modules"), function(module) {
                return models.menuItemModel({
                    id: module.id,
                    name: utils.translateName(module.name, lang, langs),
                    icon: utils.moduleIcon(module),
                    has_errors: false,
                    subitems: _.map(module.forms, function(form) {
                        return models.menuItemModel({
                            id: form.id,
                            name: utils.translateName(form.name, lang, langs),
                            icon: utils.formIcon(form),
                        });
                    }),
                });
            }),
            viewAllItems: gettext("View All Forms"),
        });

        var formSummaryContent = formSummaryModel({
            errors: initialPageData.get("errors"),
            form_name_map: initialPageData.get("form_name_map"),
            lang: lang,
            langs: langs,
            modules: initialPageData.get("modules"),
            read_only: initialPageData.get("read_only"),
        });

        models.initSummary(formSummaryMenu, formSummaryContent);
    });
});
