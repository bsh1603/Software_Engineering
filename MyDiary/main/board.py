from main import *
from flask import Blueprint

blueprint = Blueprint("board", __name__, url_prefix="/board")

@blueprint.route("/list")
def lists():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 5, type=int)

    board = mongo.db.board
    datas = board.find({}).skip((page-1) * limit).limit(limit)

    tot_count = board.find({}).count()
    last_page_num = math.ceil(tot_count / limit)

    block_size = 5
    block_num = ((page - 1) / block_size)
    block_start = int((block_size * block_num) + 1)
    block_last = math.ceil(block_start + (block_size - 1))

    return render_template("list.html", datas = datas, limit=limit, page = page, block_start = block_start, block_last = block_last, last_page_num = last_page_num)

@blueprint.route("/view/<idx>")
@login_required
def board_view(idx):
    if idx is not None:
        page = request.args.get("page")
        board = mongo.db.board
        data = board.find_one({"_id" : ObjectId(idx)})
        board.find_one_and_update({"_id":ObjectId(idx)}, {"$inc":{"view":1}}, return_document=True)

        if data is not None:
            result = {
                "id" : data.get("_id"),
                "name" : data.get("name"),
                "title" : data.get("title"),
                "contents" : data.get("contents"),
                "pubdate" : data.get("pubdate"),
                "view" : data.get("view"),
                "writer_id": data.get("writer_id", "")
            }

            return render_template("view.html", result = result, page = page, title="상세보기")
    return abort(400)

@blueprint.route("/write", methods=["GET","POST"])
@login_required
def board_write():
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board
        post = {
            "name" : name,
            "title" : title,
            "contents" : contents,
            "pubdate" : current_utc_time,
            "writer_id" : session.get("id"),
            "view" : 0,
        }

        x = board.insert_one(post)
        print(x.inserted_id)

        return redirect(url_for("board.board_view", idx = x.inserted_id))

    else:
        return render_template("write.html", title="글 작성")

@blueprint.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id":ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("board.lists"))
        else:
            if session.get("id") == data.get("writer_id"):
                return render_template("edit.html", data = data)
            else:
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("board.lists"))
    else:
        title = request.form.get("title")
        contents = request.form.get("contents")

        board = mongo.db.board
        data = board.find_one({"_id":ObjectId(idx)})
        if session.get("id") == data.get("writer_id"):
            board.update_one({"_id":ObjectId(idx)},{
                "$set" : {
                    "title" : title, "contents" : contents, 
                }
            })
            flash("수정되었습니다")
            return redirect(url_for("board.board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("board.lists"))

@blueprint.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.board
    data = board.find_one({"_id":ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        board.delete_one({"_id":ObjectId(idx)})
        flash("삭제 되었습니다")
    else:
        flash("삭제 권한이 없습니다")
    return redirect(url_for("board.lists"))