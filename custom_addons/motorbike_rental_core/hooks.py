def post_init_hook(env):
    env.ref('base.VND').sudo().write({'active': True})
