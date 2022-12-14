from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemySchema
from flask_cors import CORS
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key = True, nullable=False)
    name = db.Column(db.String, nullable= False)
    edipi = db.Column(db.Integer, nullable= False, unique= True)
    email = db.Column(db.String, unique= True)
    phone_num = db.Column(db.Integer, unique= True)
    all_issues = db.relationship('Issue', backref="member", cascade="all, delete, delete-orphan", lazy=True)

    def __init__(self, name, edipi, email, phone_num):
        self.name = name
        self.edipi = edipi
        self.email = email
        self.phone_num = phone_num


class Gear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String, nullable=False)
    nomenclature = db.Column(db.String, nullable=False)
    size = db.Column(db.String, nullable=False)
    nsn = db.Column(db.String, unique=True)
    gear_img = db.Column(db.String)

    def __init__(self, category, nomenclature, size, nsn, gear_img):
        self.category = category
        self.nomenclature = nomenclature
        self.size = size
        self.nsn = nsn
        self.gear_img = gear_img

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_nomenclature = db.Column(db.String)
    issue_size = db.Column(db.String)
    issue_nsn = db.Column(db.Integer, nullable= False)
    issue_note = db.Column(db.Text(500))
    issue_count = db.Column(db.Integer)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

    def __init__(self, issue_nomenclature, issue_size, issue_nsn, issue_note, issue_count, member_id):
        self.issue_nomenclature = issue_nomenclature
        self.issue_size = issue_size
        self.issue_nsn = issue_nsn
        self.issue_note = issue_note
        self.issue_count = issue_count
        self.member_id = member_id

class IssueSchema(ma.Schema):
    class Meta:
        fields = ('id', 'issue_nomenclature', 'issue_size', 'issue_nsn', 'issue_count', 'issue_note', 'member_id')

issue_schema = IssueSchema()
many_issue_schema = IssueSchema(many=True)

class MemberSchema(ma.Schema):
    all_issues = ma.Nested(many_issue_schema)
    class Meta:
        fields = ('id', 'name', 'edipi', 'email', 'phone_num', 'all_issues')

member_schema = MemberSchema()
many_member_schema = MemberSchema(many=True)

class GearSchema(ma.Schema):
    class Meta:
        fields = ('id', 'category', 'nomenclature', 'size', 'nsn', 'gear_img')

gear_schema = GearSchema()
many_gear_schema = GearSchema(many=True)



# EndPoints

# member/add
@app.route('/member/add', methods=['POST'])
def add_member():
    if request.content_type != 'application/json':
        return jsonify("Error Creating New Member")

    post_data = request.get_json()
    name = post_data.get('name')
    edipi = post_data.get('edipi')
    email = post_data.get('email')
    phone_num = post_data.get('phone_num')

    if edipi == None:
        return jsonify('Error: edipi is required')

    if email == None:
        return jsonify('Error: email is required')

    if phone_num == None:
        return jsonify('Error: phone_num is required')

    new_member = Member(name, edipi, email, phone_num)

    db.session.add(new_member)
    db.session.commit()

    return jsonify(member_schema.dump(new_member))

# member/get
@app.route('/member/get')
def get_members():
    all_members = db.session.query(Member).all()
    return jsonify(many_member_schema.dump(all_members))

# member/get/<id>
@app.route('/member/get/<id>')
def get_a_member(id):
    a_member = db.session.query(Member).filter(Member.id == id).first()
    return jsonify(member_schema.dump(a_member))

# member/edit
@app.route('/member/edit/<id>', methods=['PUT'])
def edit_member(id):
    if request.content_type != 'application/json':
        return jsonify('It needs JSON File')

    put_data = request.get_json()
    name = put_data.get('name')
    edipi = put_data.get('edipi')
    email = put_data.get('email')
    phone_num = put_data.get('phone_num')

    edit_member = db.session.query(Member).filter(Member.id == id).first()
    if name != None:
        edit_member.name = name
    if edipi != None:
        edit_member.edipi = edipi
    if email != None:
        edit_member.email = email
    if phone_num != None:
        edit_member.phone_num = phone_num

    db.session.commit()

    return jsonify(member_schema.dump(edit_member))

# member/delete
@app.route("/member/delete/<id>", methods=["DELETE"])
def delete_member(id):
    delete_member = db.session.query(Member).filter(Member.id == id).first()
    db.session.delete(delete_member)
    db.session.commit()

    return jsonify('member removed')

# member/add/many
@app.route('/member/add/many', methods=["POST"])
def add_many_members():
    if request.content_type != "application/json":
        return jsonify("Needs JSON File")

    post_data = request.get_json()
    members = post_data.get('members')

    new_members = []

    for member in members:
        name = member.get('name')
        edipi = member.get('edipi')
        email = member.get('email')
        phone_num = member.get('phone_num')

        existing_member_check = db.session.query(Member).filter(Member.edipi == edipi).first()
        if existing_member_check != None:
            return jsonify("member already exist")

        else:
            new_member = Member(name, edipi, email, phone_num)
            db.session.add(new_member)
            db.session.commit()
            new_members.append(new_member)

    return jsonify(many_member_schema.dump(new_members))


# issue add
@app.route("/issue/add", methods=["POST"])
def add_issue():
    if request.content_type != "application/json":
        return jsonify("needs JSON file")

    post_data = request.get_json()
    issue_nomenclature = post_data.get("issue_nomenclature")
    issue_size = post_data.get("issue_size")
    issue_nsn = post_data.get("issue_nsn")
    issue_note = post_data.get("issue_note")
    issue_count = post_data.get("issue_count")
    member_id = post_data.get("member_id")

    if issue_nsn == None:
        return jsonify("nsn needed")
    if member_id == None:
        return jsonify("member_id needed")

    new_issue = Issue(issue_nomenclature, issue_size, issue_nsn, issue_note, issue_count, member_id)
    db.session.add(new_issue)
    db.session.commit()

    return jsonify(issue_schema.dump(new_issue))

# issue/edit
@app.route("/issue/edit/<id>", methods=["PUT"])
def edit_issue(id):
    if request.content_type != 'application/json':
        return jsonify('needs to be JSON')

    put_data = request.get_json()
    issue_nomenclature = put_data.get("issue_nomenclature")
    issue_size = put_data.get("issue_size")
    issue_nsn = put_data.get("issue_nsn")
    issue_note = put_data.get("issue_note")
    issue_count = put_data.get("issue_count")

    edit_issue = db.session.query(Issue).filter(Issue.id == id).first()
    if issue_nomenclature != None:
        edit_issue.issue_nomenclature = issue_nomenclature
    if issue_size != None:
        edit_issue.issue_size = issue_size
    if issue_nsn != None:
        edit_issue.issue_nsn = issue_nsn
    if issue_note != None:
        edit_issue.issue_note = issue_note
    if issue_count != None:
        edit_issue.issue_count = issue_count

    db.session.commit()

    return jsonify(issue_schema.dump(edit_issue))

# delete/issue
@app.route('/issue/delete/<id>', methods=["DELETE"])
def delete_issue(id):
    delete_issue = db.session.query(Issue).filter(Issue.id == id).first()
    db.session.delete(delete_issue)
    db.session.commit()

    return jsonify("record DELDETED")

# add many issues
@app.route('/issue/add/many', methods=['POST'])
def add_many_issues():
    if request.content_type != 'application/json':
        return jsonify('needs to be JSON')

    post_data = request.get_json()
    issues = post_data.get('issues')

    new_issues = []

    for issue in issues:
        issue_nomenclature = issue.get('issue_nomenclature')
        issue_size = issue.get('issue_size')
        issue_nsn = issue.get('issue_nsn')
        issue_note = issue.get('issue_note')
        issue_count = issue.get('issue_count')
        member_id = issue.get('member_id')

        if issue_nsn == None:
            return jsonify("nsn needed")
        if member_id == None:
            return jsonify("member_id needed")

        new_issue = Issue(issue_nomenclature, issue_size, issue_nsn, issue_note, issue_count, member_id)
        db.session.add(new_issue)
        db.session.commit()
        new_issues.append(new_issue)

    return jsonify(many_issue_schema.dump(new_issues))

# gear post
@app.route("/gear/add", methods=["POST"])
def add_gear():
    if request.content_type != "application/json":
        return jsonify("must be a JSON file")

    post_data = request.get_json()
    category = post_data.get('category')
    nomenclature = post_data.get('nomenclature')
    size = post_data.get('size')
    nsn = post_data.get('nsn')
    gear_img = post_data.get('gear_img')

    if category == None:
        return jsonify('Error: category is required my guy or miss whatever you are')
    if nomenclature == None:
        return jsonify('Error: nomenclature is required my guy or miss whatever you are')
    if size == None:
        return jsonify('Error: size is required my guy or miss whatever you are')
    if nsn == None:
        return jsonify('Error: category is required my guy or miss whatever you are')

    new_gear = Gear(category, nomenclature, size, nsn, gear_img)

    db.session.add(new_gear)
    db.session.commit()

    return jsonify(gear_schema.dump(new_gear))

# gear/get
@app.route("/gear/get")
def get_gears():
    all_gears = db.session.query(Gear).all()
    return jsonify(many_gear_schema.dump(all_gears))

# gear/get/one
@app.route("/gear/get/<id>")
def get_one_gear(id):
    one_gear = db.session.query(Gear).filter(Gear.id == id).first()
    return jsonify(gear_schema.dump(one_gear))

# gear/edit
@app.route("/gear/edit/<id>", methods=["PUT"])
def edit_gear(id):
    if request.content_type != 'application/json':
        return jsonify('it has to be JSON File')

    put_data = request.get_json()
    category = put_data.get('category')
    nomenclature = put_data.get('nomenclature')
    size = put_data.get('size')
    nsn = put_data.get('nsn')
    gear_img = put_data.get('gear_img')

    edit_gear = db.session.query(Gear).filter(Gear.id == id).first()
    if category != None:
        edit_gear.category = category
    if nomenclature != None:
        edit_gear.nomenclature = nomenclature
    if size != None:
        edit_gear.size = size
    if nsn != None:
        edit_gear.nsn = nsn
    if gear_img != None:
        edit_gear.gear_img = gear_img
    
    db.session.commit()

    return jsonify(gear_schema.dump(edit_gear))

# gear/delete
@app.route("/gear/delete/<id>", methods=["DELETE"])
def delete_gear(id):
    delete_gear = db.session.query(Gear).filter(Gear.id == id).first()
    db.session.delete(delete_gear)
    db.session.commit()

    return jsonify('Gear Record DELETED')

# gear/add/many
@app.route('/gear/add/many', methods=['POST'])
def add_many_gears():
    if request.content_type != 'application/json':
        return jsonify('needs to be JSON')

    post_data = request.get_json()
    gears = post_data.get('gears')

    new_gears = []

    for gear in gears:
        category = gear.get('category')
        nomenclature = gear.get('nomenclature')
        size = gear.get('size')
        nsn = gear.get('nsn')
        gear_img = gear.get('gear_img')

        existing_gear_check = db.session.query(Gear).filter(Gear.nsn == nsn).first()
        if existing_gear_check != None:
            return jsonify("gear already exist")

        else:
            new_gear = Gear(category, nomenclature, size, nsn, gear_img)
            db.session.add(new_gear)
            db.session.commit()
            new_gears.append(new_gear)

    return jsonify(many_gear_schema.dump(new_gears))


if __name__ == "__main__":
    app.run(debug = True)
