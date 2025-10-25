# -*- coding: utf-8 -*-
{
    "name": """Ecommerce SEO URLs | Product & Category URL Rewriter""",
    "summary": """You have the flexibility to personalize product and shop page URLs, 
                making them independent of the product's name or ID. 
                Basically you can have either the product name or Product ID on the URLs for SEO purposes, Product URL Change, Product URL Customization, Product URL SEO, Product URL Optimization, Product URL Management, Product ID Remover, Product ID Change, Product ID Customization, Product ID SEO, Product ID Optimization, Product ID Management, Product ID Remover, Product URL Arabic Language, Product URL Arabic, Product URL Arabic SEO, Product URL Arabic Optimization, Product URL Arabic Management, Product ID Arabic, Product ID Arabic SEO, Product ID Arabic Optimization, Product ID Arabic Management, Website Product URL, Website Product URL Change, Website Product URL Customization, Website Product URL SEO, Website Product URL Optimization, Website Product URL Management, Website Product ID Remover, Website Product ID Change, Website Product ID Customization, Website Product ID SEO, Website Product ID Optimization, Website Product ID Management, Website Product ID Remover, Website Product URL Arabic, Website Product URL Arabic SEO, Website Product URL Arabic Optimization, Website Product URL Arabic Management, Website Product ID Arabic, Website Product ID Arabic SEO, Website Product ID Arabic Optimization, Website Product ID Arabic Management""",
    "description": """Customize your product and shop page URLs effortlessly, 
                        decoupling them from specific product names or IDs. 
                        Enjoy the flexibility to craft distinct web addresses that resonate with your brand. 
                        This feature not only enhances your website's structure but also boosts SEO and improves the overall user experience. 
                        Take charge of your online presence with personalized product page URLs, making navigation smoother for your customers.""",
    "category": "eCommerce",
    "version": "18.0",
    "author": "EWall Solutions Pvt. Ltd.",
    "support": "support@ewallsolutions.com",
    "website": "http://www.ewallsolutions.com",
    'maintainer': 'EWall Solutions Pvt. Ltd.',
    'company': "EWall Solutions Pvt. Ltd. ",
    'currency':'USD',
    'license': 'OPL-1',
    'price':'57.00',
    "depends": ["base", "product","website_sale"],
    "external_dependencies": {"python": [], "bin": []},
    "data": ["views/product_seo_url.xml","views/product_category_seo_url_template.xml"],
    'images': [
        'static/description/images/banner.png',
    ],
    "post_load": "post_load",
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
}
