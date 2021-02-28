# coding=utf-8
# author: Dimbiniaina Rafanoharana
# 20210228

import asn1tools
import os
import sys

buildingTypes =[
    'ANY',
    'INTEGER',
    'BOOLEAN',
    'NULL',
    'ENUMERATED',
    'REAL',
    'BIT STRING',
    'OCTET STRING',
    'CHOICE',
    'SEQUENCE',
    'SET',
    'SEQUENCE OF',
    'SET OF',
    'OBJECT IDENTIFIER',
    'UTF8String',
    'GeneralString',
    'NumericString',
    'PrintableString',
    'IA5String',
    'GraphicString',
    'GeneralizedTime',
    'UTCTime',
    'ObjectDescriptor',  
    'VisibleString',
    'TeletexString',
    'UniversalString',
    'BMPString',
    'T61String',
    'VideotexString'
]

getPrimitiveOrConstructedType={
    'ANY': 'Constructed',
    'INTEGER': 'Primitive',
    'BOOLEAN': 'Primitive',
    'NULL': 'Primitive',
    'ENUMERATED': 'Primitive',
    'REAL': 'Primitive',
    'BIT STRING': 'Primitive',
    'OCTET STRING': 'Primitive',
    'CHOICE': 'Constructed',
    'SEQUENCE': 'Constructed',
    'SET': 'Constructed',
    'SEQUENCE OF': 'Constructed',
    'SET OF': 'Constructed',
    'OBJECT IDENTIFIER': 'Primitive',
    'UTF8String': 'Primitive',
    'GeneralString': 'Primitive',
    'NumericString': 'Primitive',
    'PrintableString': 'Primitive',
    'IA5String': 'Primitive',
    'GraphicString': 'Primitive',
    'GeneralizedTime': 'Primitive',
    'UTCTime': 'Primitive',
    'ObjectDescriptor': 'Primitive',  
    'VisibleString': 'Primitive',
    'TeletexString': 'Primitive',
    'UniversalString': 'Primitive',
    'BMPString': 'Primitive',
    'T61String': 'Primitive',
    'VideotexString': 'Primitive',
}

pyAsn1BuildinTypes = {
    'ANY': 'univ.Any',
    'INTEGER': 'univ.Integer',
    'BOOLEAN': 'univ.Boolean',
    'NULL': 'univ.Null',
    'ENUMERATED': 'univ.Enumerated',
    'REAL': 'univ.Real',
    'BIT STRING': 'univ.BitString',
    'OCTET STRING': 'univ.OctetString',
    'CHOICE': 'univ.Choice',
    'SEQUENCE': 'univ.Sequence',
    'SET': 'univ.Set',
    'SEQUENCE OF': 'univ.SequenceOf',
    'SET OF': 'univ.SetOf',
    'OBJECT IDENTIFIER': 'univ.ObjectIdentifier',
    'UTF8String': 'char.UTF8String',
    'GeneralString': 'char.GeneralString',
    'NumericString': 'char.NumericString',
    'PrintableString': 'char.PrintableString',
    'IA5String': 'char.IA5String',
    'GraphicString': 'char.GraphicString',
    'GeneralizedTime': 'useful.GeneralizedTime',
    'UTCTime': 'useful.UTCTime',
    'ObjectDescriptor': 'useful.ObjectDescriptor',  # In pyasn1 r1.2
    'VisibleString': 'char.VisibleString',
    'TeletexString': 'char.TeletexString',
    'UniversalString': 'char.UniversalString',
    'BMPString': 'char.BMPString',
    'T61String': 'char.T61String',
    'VideotexString': 'char.VideotexString',
}

def getTagNumber(tagSpec):
    pyAsn1TagNumber = tagSpec['number']    
    return pyAsn1TagNumber

def getTagClass(tagSpec):
    pyAsn1TagContexts = {
        'APPLICATION': 'tag.tagClassApplication',
        'PRIVATE': 'tag.tagClassPrivate',
        'UNIVERSAL': 'tag.tagClassUniversal'
    }
    """ If the class name is absent, then the tag is context- specific. 
    Context-specific tags can only appear in a component of a structured or CHOICE type. 
    Ref: http://luca.ntop.org/Teaching/Appunti/asn1.html
    """
    # Par défaut, le tagClass est du type tagClassContext
    pyAsn1TagClass = 'tag.tagClassContext'
    if 'class' in tagSpec:
        pyAsn1TagClass = pyAsn1TagContexts.get(tagSpec['class'], 'tag.tagClassContext')     
    return pyAsn1TagClass

def getVariableBuiltInType(spec, variableType):
    if variableType in buildingTypes:
        variableBuildinType = variableType
        return variableBuildinType 
    elif variableType in spec['types']:
        variableBuildinType = spec['types'][variableType]['type']
        if variableBuildinType in buildingTypes:
            return variableBuildinType
        else: 
            return getVariableBuiltInType(spec, variableBuildinType)
    else:
        raise Exception('Le buildinType du variable {} n\'est pas défini'.format(variableType))
        
def getTagFormat(spec, variableType):
    variableBuildinType = getVariableBuiltInType(spec, variableType)    
    ConstructedOrPrimitive = getPrimitiveOrConstructedType.get(variableBuildinType)
    pyAsn1TagFormat = 'tag.tagFormatSimple'
    if ConstructedOrPrimitive == 'Constructed':
        pyAsn1TagFormat = 'tag.tagFormatConstructed'
    elif ConstructedOrPrimitive == 'Primitive':
        pyAsn1TagFormat = 'tag.tagFormatSimple'        
    return pyAsn1TagFormat

def getImplicitness(spec, dictSpec):
    equivAsn1CryptoImplicitness = {
        'IMPLICIT': 'implicitTag',
        'EXPLICIT': 'explicitTag'
    }
    """ The keyword [class number] alone is the same as explicit tagging, 
    except when the "module" in which the ASN.1 type is defined has implicit 
    tagging by default. ("Modules" are among the advanced features not described in this note.) 
    Ref: http://luca.ntop.org/Teaching/Appunti/asn1.html
    """
    # Default implicitness is EXPLICIT 
    implicitness = equivAsn1CryptoImplicitness.get('EXPLICIT')
    # Check if implicitness is defined in the module
    if 'tags' in spec.keys():
        try:
            implicitness = equivAsn1CryptoImplicitness[spec['tags']]
        except:
            raise Exception('L\'implicitness du variable {} n\'est ni \'IMPLICIT\' ni \'EXPLICIT\' '.format(spec['tags']))
    # Check if implicitness is defined in [class number] EX/IMPLICITNESS      
    elif 'tag' in dictSpec:
        try:
            implicitness = equivAsn1CryptoImplicitness[dictSpec['tags']]
        except:
            raise Exception('L\'implicitness du variable {} n\'est ni \'IMPLICIT\' ni \'EXPLICIT\' '.format(dictSpec['tags']))
    return implicitness

def buildTagConfig(spec, memberSpec):
    """ An ASN.1 tag could be viewed as a tuple of three numbers: (Class, Format, Number).
        While Number identifies a tag, Class component is used to create scopes for Numbers. 
        Four scopes are currently defined: UNIVERSAL, CONTEXT (context-specific), APPLICATION and PRIVATE. 
        The Format component is actually a one-bit flag - zero for tags associated with scalar types,
        and one for constructed types (will be discussed later on).
        Ref: https://www.digital-experts.de/doc/python-pyasn1/pyasn1-tutorial.html

        e.g: ASN1 
        ASN.1 notation:

        [[class] number] IMPLICIT Type

        class = UNIVERSAL | APPLICATION | PRIVATE

        where Type is a type, class is an optional class name, and number is the tag number within the class, 
        a nonnegative integer.
    """
    pyAsn1TagFormat = getTagFormat(spec, memberSpec['type'])
    pyAsn1TagContext = getTagClass(memberSpec['tag']) 
    pyAsn1TagNumber = getTagNumber(memberSpec['tag'])
    pyAsn1TagImplicitness = getImplicitness(spec, memberSpec)
    return '{} = tag.Tag({}, {}, {})'.format(pyAsn1TagImplicitness, pyAsn1TagContext, 
                                             pyAsn1TagFormat, pyAsn1TagNumber)

def getInlineMemberType(memberSpec):
    asn1MemberType = memberSpec['type']
    pyAsn1MemberType = pyAsn1BuildinTypes.get(asn1MemberType, asn1MemberType) + '()' 
    if asn1MemberType == 'SET OF':
        memberType = 'univ.SetOf(componentType={})'.format(pyAsn1BuildinTypes.get(
            memberSpec['element']['type'],memberSpec['element']['type']) + '()') 
        # Size constraint n'est pas encore implémenté
    elif asn1MemberType == 'SEQUENCE OF':
        memberType = 'univ.SequenceOf(componentType={})'.format( 
            pyAsn1BuildinTypes.get(memberSpec['element']['type'],memberSpec['element']['type']) + '()')   
        # Size constraint n'est pas encore implémenté
    else:
        memberType = pyAsn1MemberType 
        if 'default' in memberSpec:
            if memberSpec['default'] is not None:
                defaultValue = memberSpec['default']
                memberType =   pyAsn1MemberType + '({})'.format(defaultValue)                
    return memberType

def buildMemberType(spec, memberSpec):    
    return '{}.subtype({})'.format(getInlineMemberType(memberSpec), buildTagConfig(spec, memberSpec))
    
def buildComponent(spec, memberSpec):
    memberName = memberSpec['name']
    memberType = buildMemberType(spec, memberSpec)
    if 'optional' in memberSpec:
        return 'namedtype.OptionalNamedType(\'{}\', {})'.format(memberName, memberType)
    elif 'default' in memberSpec:
        defaultValue = memberSpec['default']
        return 'namedtype.DefaultedNamedType(\'{}\', {})'.format(memberName, memberType)
    else:
        return 'namedtype.NamedType(\'{}\', {})'.format(memberName, memberType)

def buildConstructedVariable(spec, dictSpec, variableName):
    className = variableName
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpec['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)    
    componentHeader = '{}componentType = namedtype.NamedTypes( \n'.format(indent)
    componentBody = ',\n'.join([indent*2 + buildComponent(spec,member) for member in dictSpec['members']])
    componentBottom =  ')\n\n'
    return head + componentHeader + componentBody + componentBottom 

def buildSetVariable(spec, dictSpecSet, nameSet):
    className = nameChoice
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecSet['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(classChoice, variableAsn1CryptoType)    
    componentHeader = '{}componentType = namedtype.NamedTypes( \n'.format(indent)
    componentBody = ',\n'.join([indent*2 + buildComponent(spec,member) for member in dictSpecSet['members']])
    componentBottom =  ')\n\n'
    return head + componentHeader + componentBody + componentBottom 

def buildSequenceVariable(spec, dictSpecSequence, nameSequence):
    className = nameSequence
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecSequence['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)    
    componentHeader = '{}componentType = namedtype.NamedTypes( \n'.format(indent)
    componentBody = ',\n'.join([indent*2 + buildComponent(spec,member) for member in dictSpecSequence['members']])
    componentBottom =  ')\n\n'
    return head + componentHeader + componentBody + componentBottom 

def buildSequenceOfVariable(spec, dictSpecSequenceOf, nameSequenceOf):
    className = nameSequenceOf
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecSequenceOf['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)    
    component = '{}componentType = {} \n\n\n'.format(indent, dictSpecSequenceOf['element']['type'])
    return head + component

def buildChoiceVariable(spec, dictSpecChoice, nameChoice):
    className = nameChoice
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecChoice['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)    
    componentHeader = '{}componentType = namedtype.NamedTypes( \n'.format(indent)
    componentBody = ',\n'.join([indent*2 + buildComponent(spec,member) for member in dictSpecChoice['members']])
    componentBottom =  ')\n\n\n' 
    return head + componentHeader + componentBody + componentBottom 

def buildEnumeratedVariable(spec, dictSpecEnumerated, nameEnumerated):
    className = nameEnumerated
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecEnumerated['type'])
    indent = ' ' * 4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)
    bottom = '{}pass  \n\n'.format(indent)
    valuesHeader = '{}.namedValues = namedval.NamedValues( \n'.format(className)  
    valuesMember = ',\n'.join(['{}(\'{}\', {})'.format(indent, member[0], member[1]) for member in dictSpecEnumerated['values']])
    valuesBottom = '\n ) \n\n\n'
    values = valuesHeader + valuesMember + valuesBottom    
    return head + bottom + values

def buildUTF8StringVariable(spec, dictSpecUTF8String, nameUTF8String):
    def buildUTF8StringConstraint(dictSpecUTF8String, className):
        constraint = '\n'
        if 'size' in dictSpecUTF8String.keys():
            if type(dictSpecUTF8String['size'][0]) == int:
                constraintMinVal, constraintMaxVal = dictSpecUTF8String['size'][0], dictSpecUTF8String['size'][0]
            elif type(dictSpecUTF8String['size'][0]) == tuple:
                constraintMinVal, constraintMaxVal = dictSpecUTF8String['size'][0][0], dictSpecUTF8String['size'][0][1]
            constraint = '{}.subtypeSpec = constraint.ValueSizeConstraint({}, {}) \n\n'.format(className, constraintMinVal, constraintMaxVal)
        return constraint 
    className = nameUTF8String
    indent = ' '*4
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecUTF8String['type'])
    head = "class {}({}): \n".format(className, variableAsn1CryptoType)
    bottom = "{}pass  \n\n\n".format(indent)
    constraint = buildUTF8StringConstraint(dictSpecUTF8String, className)    
    return head + bottom + constraint

def buildIA5StringVariable(spec, dictSpecIA5String, nameIA5String):
    def buildIA5StringConstraint(dictSpecIA5String, className):
        constraint = '\n'
        if 'size' in dictSpecIA5String.keys():
            if type(dictSpecIA5String['size'][0]) == int:
                constraintMinVal, constraintMaxVal = dictSpecIA5String['size'][0], dictSpecIA5String['size'][0]
            elif type(dictSpecIA5String['size'][0]) == tuple:
                constraintMinVal, constraintMaxVal = dictSpecIA5String['size'][0][0], dictSpecIA5String['size'][0][1]
            constraint = '{}.subtypeSpec = constraint.ValueSizeConstraint({}, {}) \n\n\n'.format(className, constraintMinVal, constraintMaxVal)
        return constraint 
    className = nameIA5String
    indent = ' '*4
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecIA5String['type'])
    head = "class {}({}): \n".format(className, variableAsn1CryptoType)
    bottom = "{}pass  \n\n\n".format(indent)
    constraint = buildIA5StringConstraint(dictSpecIA5String, className)    
    return head + bottom + constraint

def buildIntegerVariable(spec, dictSpecInteger, nameInteger):
    def buildIntegerConstraint(dictSpecInteger, className):
        constraint = '\n'
        if 'restricted-to' in dictSpecInteger.keys():
            if type(dictSpecInteger['restricted-to'][0]) == int:
                constraintMinVal, constraintMaxVal = dictSpecInteger['restricted-to'][0], dictSpecInteger['restricted-to'][0]
            elif type(dictSpecInteger['restricted-to'][0]) == tuple:
                constraintMinVal, constraintMaxVal = dictSpecInteger['restricted-to'][0][0], dictSpecInteger['restricted-to'][0][1]
            constraint = '{}.subtypeSpec = constraint.ValueRangeConstraint({}, {}) \n\n\n'.format(className, constraintMinVal, constraintMaxVal)
        return constraint 
    className = nameInteger
    indent = ' '*4
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpecInteger['type'])
    head = "class {}({}): \n".format(className, variableAsn1CryptoType)
    bottom = "{}pass  \n\n\n".format(indent)
    constraint = buildIntegerConstraint(dictSpecInteger, className)    
    return head + bottom + constraint

def buildClassicVariable(spec, dictSpec, name):
    className = name
    variableAsn1CryptoType = pyAsn1BuildinTypes.get(dictSpec['type'], dictSpec['type'])
    indent = ' '*4
    head = 'class {}({}): \n'.format(className, variableAsn1CryptoType)    
    component = '{}pass \n\n\n'.format(indent)
    return head + component

def buildVariable(spec, dictSpec, variable): 
    if dictSpec['type'] == 'INTEGER':
        m = buildIntegerVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'IA5String':
        m = buildIA5StringVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'ENUMERATED': 
        m = buildEnumeratedVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'CHOICE':
        m = buildChoiceVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'UTF8String':
        m = buildUTF8StringVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'SEQUENCE':
        m = buildSequenceVariable(spec, dictSpec, variable)
    elif dictSpec['type'] == 'SEQUENCE OF' or dictSpec['type'] == 'SET OF':
        m = buildSequenceOfVariable(spec, dictSpec, variable)
    else:
        m = buildClassicVariable(spec, dictSpec, variable)    
    return m 

def dataStructGenFromSpec(spec):
    for module in spec:
        moduleSpec = spec[module]
        listVariables = [variable for variable in moduleSpec['types']]
        n = ''
        listVariablesDefinies = set(buildInType for buildInType in pyAsn1BuildinTypes.keys())
        k = 0
        while len(listVariables) + len(pyAsn1BuildinTypes) != len(listVariablesDefinies):
            if k > len(listVariables):
                break
            for variableType in listVariables:
                # Si la variable est déjà definie alors on passe au suivant 
                if variableType in listVariablesDefinies:
                    continue
                variableSpec = moduleSpec['types'][variableType]
                if getPrimitiveOrConstructedType.get(variableSpec['type']) == 'Constructed':
                    variableSpec = moduleSpec['types'][variableType]
                    # Prends la liste des variables qui doivent etre definies avant de pouvoir définir la variable elle meme
                    listeMembersType = []
                    if variableSpec['type'] == 'SEQUENCE OF' or variableSpec['type'] == 'SET OF':
                        listeMembersType += [variableSpec['element']['type']]
                    else:
                        for member in variableSpec['members']: 
                            if member['type'] == 'SEQUENCE OF' or member['type'] == 'SET OF':
                                listeMembersType += [member['element']['type']]
                            else: 
                                listeMembersType += [member['type']]
                    # Si une ou plusieurs varibles requises ne sont pas encore définies alors on passe à une autre variable
                    var = True
                    for member in listeMembersType:
                        if member not in listVariablesDefinies:     
                            var = False
                            break
                    if var == True:               
                        n += buildVariable(moduleSpec, moduleSpec['types'][variableType], variableType)
                        listVariablesDefinies.add(variableType)
                if getPrimitiveOrConstructedType.get(variableSpec['type']) != 'Constructed':
                    try: 
                        n += buildVariable(moduleSpec, moduleSpec['types'][variableType], variableType)
                        listVariablesDefinies.add(variableType)
                    except Exception as es:
                        print('Error : {}'.format(es))
            k += 1
        with open("{}.py".format(module), 'w' ,newline='') as file:
            file.write("# {} PyAsn1 data structure \n".format(module) )
            file.write("from pyasn1.type import univ, char, namedtype, namedval, tag, constraint, useful \n\n\n")
            file.write(n)

def dataStructGenFromFile(nomFichier):
    fileSpec = asn1tools.parse_files(nomFichier)
    dataStructGenFromSpec(fileSpec) 

if __name__ == '__main__':
    dataStructGenFromFile(sys.argv[1])

