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
    issue_nsn = db.Column(db.String)
    issue_note = db.Column(db.Text(500))
    issue_count = db.Column(db.Integer)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

    def __init__(self, issue_nomenclature, issue_size, issue_nsn, issue_note, issue_count, user_id):
        self.issue_nomenclature = issue_nomenclature
        self.issue_size = issue_size
        self.issue_nsn = issue_nsn
        self.issue_note = issue_note
        self.issue_count = issue_count
        self.user_id = user_id

class IssueSchema(ma.Schema):
    class Meta:
        fields = ('id', 'issue_nomenclature', 'issue_size', 'issue_nsn', 'issue_note', 'member_id')

issue_schema = IssueSchema()
many_issue_schema = IssueSchema(many=True)

class MemberSchema(ma.Schema):
    all_issues = ma.Nested(many_issue_schema)
    class Meta:
        fields = ('id', 'name', 'edipi', 'email', 'phone_num')

member_schema = MemberSchema()
many_member_schema = MemberSchema(many=True)

class Gear(ma.Schema):
    class Meta:
        fields = ('id', 'category', 'nomenclature', 'size', 'nsn', 'gear_img')


# EndPoints

# user/add
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
        if existing_member_check is None:
            new_member = Member(name, edipi, email, phone_num)
            db.session.add(new_member)
            db.session.commit()
            new_members.append(new_member)

        return jsonify(many_member_schema.dump(new_members))

if __name__ == "__main__":
    app.run(debug = True)
