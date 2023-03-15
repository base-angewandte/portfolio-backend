from django import template

register = template.Library()


@register.simple_tag
def must_have(fieldname, value):
    if not value:
        raise ValueError(f'Field {fieldname!r} is mandatory.')
    return ''


@register.simple_tag
def any_must_match(list_value, args):
    def get_nested_prop(arg, path: list):
        if len(path) == 1:
            # print("\tFOUND ", path[0], '=', arg.get(path[0]))
            return arg.get(path[0])

        if isinstance(arg, dict) and path[0] in arg:
            # print('\t\t', path)
            return get_nested_prop(arg.get(path[0]), path[1:])

        if isinstance(arg, list):
            return [get_nested_prop(item, path) for item in arg]

        return

    if list_value:
        conditions = args.split(';')
        # print("CONDITIONS", conditions)

        for _i, item in enumerate(list_value):
            # print(_i, item)
            # all the conditions must be satisfied for an item to qualify
            conditions_met = []
            for cond in conditions:
                field_name, field_val = cond.split('=')
                # print("COND", cond)
                # First attribute in property path is omitted as it's passed to the template tag
                matches = get_nested_prop(item, field_name.split('.')[1:])
                # print("MATCHES", matches)
                conditions_met.append(matches is not None and field_val in matches)

            # print(_i, "CONDITIONS_MET", conditions_met)
            if all(conditions_met):
                return ''

    raise ValueError(args)
